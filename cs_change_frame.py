# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

from bpy.types import AddonPreferences, Operator
from bpy.props import FloatProperty, BoolProperty
import bpy
bl_info = {
    "name": "Change Frame",
    "author": "Cenek Strichel",
    "version": (1, 0, 5),
    "blender": (2, 80, 0),
    "location": "Add 'view3d.change_frame_drag' to Input Preferences under 3D View (Global)",
    "description": "Change frame by dragging",
    "category": "Cenda Tools",
    "wiki_url": "https://github.com/CenekStrichel/CendaTools/wiki",
    "tracker_url": "https://github.com/CenekStrichel/CendaTools/issues"
}

is28 = bool(bpy.app.version >= (2, 80, 0))
is27 = bool(bpy.app.version < (2, 80, 0))

if (is27):
    context_prefs = '''bpy.context.user_preferences.addons[%r].preferences''' % __name__
    sym = ' = '
if (is28):
    context_prefs = '''bpy.context.preferences.addons[%r].preferences''' % __name__
    sym = ': '

# ==========================================================
bprops = [
    'BoolProperty',
    'BoolVectorProperty',
    'IntProperty',
    'IntVectorProperty',
    'FloatProperty',
    'FloatVectorProperty',
    'StringProperty',
    'EnumProperty',
    'PointerProperty',
    'CollectionProperty',
    'RemoveProperty',
    ]
bprops = [eval('bpy.props.%s' % b) for b in bprops]


def register_props(cls):
    txt = ''

    if type(cls) is type:
        # blank class
        name = cls.__name__
        for var in cls.__dict__:
            prop = cls.__dict__[var]
            if not prop or type(prop) is not tuple:
                continue

            # if prop[0] in bpy.props.__dict__.items():
                #   # This version includes the Properties plus hidden props, that you'd never run into anyway; either one works
            if prop[0] in bprops:
                txt += "%s%s%s.%s; " % (var, sym, name, var)
    return txt
# ==========================================================


class CENDA_OT_ChangeFrame(Operator):

    """Change frame with dragging"""
    bl_idname = "view3d.change_frame_drag"
    bl_label = "Change Frame Drag"
    bl_options = {'UNDO_GROUPED', 'INTERNAL', 'GRAB_CURSOR', 'BLOCKING'}

    class props:
        autoSensitivity = BoolProperty(name="Auto Sensitivity")
        defaultSensitivity = FloatProperty(name="Sensitivity", default=5)
        renderOnly = BoolProperty(name="Render Only", default=True)
    exec(register_props(props))

    global frameOffset
    global mouseOffset
    global sensitivity
    global previousManipulator
    global previousOnlyRender
    global StartButton

    def modal(self, context, event):

        addon_prefs = eval(context_prefs)
        scene = context.scene
        space_data = context.space_data

        # change frame
        if (event.type == 'MOUSEMOVE'):

            delta = self.mouseOffset - event.mouse_x

            if (addon_prefs.boolSmoothDrag):
                off = (-delta * self.sensitivity) + self.frameOffset
                current = int(off)
                subframe = off - int(off)
                if (current < 0 and subframe) or subframe < 0:
                    # Negative numbers have to offset a little for frame_set
                    current -= 1
                    subframe = 1 - abs(subframe)
                scene.frame_current = current
                scene.frame_subframe = subframe

            else:
                scene.frame_current = (-delta * self.sensitivity) + self.frameOffset

        # end of modal
        elif (event.type == self.startButton and event.value == 'RELEASE'):

            # previous viewport setting
            if (context.area.type == 'VIEW_3D'):
                if is27:
                    space_data.show_manipulator = self.previousManipulator

                    if (self.renderOnly):
                        space_data.show_only_render = self.previousOnlyRender
                if is28:
                    space_data.show_gizmo = self.previousManipulator

                    if (self.renderOnly):
                        space_data.overlay.show_overlays = self.previousOnlyRender

            # cursor back
            context.window.cursor_set("DEFAULT")

            # snap back
            if (addon_prefs.boolSmoothSnap):
                scene.frame_subframe = 0

            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        addon_prefs = eval(context_prefs)
        scene = context.scene
        space_data = context.space_data

        # hide viewport helpers
        if (context.area.type == 'VIEW_3D'):
            if (is27):
                self.previousManipulator = space_data.show_manipulator
                space_data.show_manipulator = False
            if (is28):
                self.previousManipulator = space_data.show_gizmo
                space_data.show_gizmo = False

            if (self.renderOnly):
                if is27:
                    self.previousOnlyRender = space_data.show_only_render
                    space_data.show_only_render = True
                if is28:
                    self.previousOnlyRender = space_data.overlay.show_overlays
                    space_data.overlay.show_overlays = False

        # start modal
        if (addon_prefs.boolSmoothDrag):
            self.frameOffset = scene.frame_current_final
        else:
            self.frameOffset = scene.frame_current

        self.mouseOffset = event.mouse_x
        self.startButton = event.type

        # cursor
        context.window.cursor_set("SCROLL_X")

        context.window_manager.modal_handler_add(self)

        found = False

        # auto sensitivity
        if (self.autoSensitivity):

            ratio = (1024 / context.area.width)
            self.sensitivity = (ratio / 10)

            # finding end of frame range
            if (scene.use_preview_range):
                endFrame = scene.frame_preview_end
            else:
                endFrame = scene.frame_end

            self.sensitivity *= (endFrame / 100)

            found = True

        # default
        if (not found):
            self.sensitivity = self.defaultSensitivity / 100

        return {'RUNNING_MODAL'}


class ChangeFrameDragAddonPreferences(AddonPreferences):

    bl_idname = __name__

    class props:
        boolSmoothDrag = BoolProperty(name="Smooth Drag", default=True)
        boolSmoothSnap = BoolProperty(name="Snap after drag", default=True)
    exec(register_props(props))

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'boolSmoothDrag')

        if (self.boolSmoothDrag):
            layout.prop(self, 'boolSmoothSnap')


classes = (
    CENDA_OT_ChangeFrame,
    ChangeFrameDragAddonPreferences,
    )


register, unregister = bpy.utils.register_classes_factory(classes)
