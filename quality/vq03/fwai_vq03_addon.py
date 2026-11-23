bl_info = {
    "name": "Future Works AI Studio — VQ03",
    "author": "Future Works AI Studio",
    "version": (0,3,0),
    "blender": (5,3,0),
    "location": "3D View > Sidebar (N) > Future Works",
    "description": "Local engineering review of 6ft5in mech, Nissan proxy, and vinyl three-pose timeline",
    "category": "3D View",
}
import bpy, os
from bpy.props import IntProperty
POC_DIR = os.path.join(os.path.expanduser("~"),"Documents","futureworks-vq03","proof-v5")
HEIGHT_METERS = 1.9558
class FWAI_OT_jump_pose(bpy.types.Operator):
    bl_idname = "fwai.jump_pose"
    bl_label = "Jump to pose"
    bl_options = {"REGISTER","UNDO"}
    frame: IntProperty(default=1,min=1,max=72)
    def execute(self, context):
        context.scene.frame_set(self.frame)
        rig = bpy.data.objects.get("FWAI-M001 / 6ft5in RIG / VQ03")
        if rig:
            for obj in context.selected_objects:obj.select_set(False)
            rig.select_set(True);context.view_layer.objects.active=rig
        self.report({"INFO"},f"Future Works: pose frame {self.frame}")
        return {"FINISHED"}
class FWAI_OT_open_review(bpy.types.Operator):
    bl_idname = "fwai.open_review"
    bl_label = "Open Review Assets"
    bl_options = {"REGISTER"}
    def execute(self, context):
        if os.path.isdir(POC_DIR):
            os.startfile(POC_DIR)
            return {"FINISHED"}
        self.report({"WARNING"},"VQ03 proof folder not found")
        return {"CANCELLED"}
class FWAI_OT_select_rig(bpy.types.Operator):
    bl_idname = "fwai.select_rig"
    bl_label = "Select Rig / Show Controls"
    bl_options = {"REGISTER","UNDO"}
    def execute(self, context):
        rig=bpy.data.objects.get("FWAI-M001 / 6ft5in RIG / VQ03")
        if not rig:return {"CANCELLED"}
        bpy.ops.object.mode_set(mode="OBJECT") if context.object and context.object.mode != "OBJECT" else None
        bpy.ops.object.select_all(action="DESELECT")
        rig.select_set(True);context.view_layer.objects.active=rig
        rig.show_in_front=True
        rig.data.display_type="STICK"
        self.report({"INFO"},"Pose control: select IK TARGET empties to adjust hand/foot positions")
        return {"FINISHED"}
class FWAI_PT_control(bpy.types.Panel):
    bl_label="Future Works — VQ03"
    bl_idname="FWAI_PT_control"
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Future Works"
    def draw(self,context):
        layout=self.layout
        col=layout.column(align=True)
        col.label(text="FWAI-M001 · Visual canon V2", icon="ARMATURE_DATA")
        col.label(text="Locked height: 6 ft 5 in")
        col.label(text="Metric: 1.9558 meters")
        col.separator()
        col.label(text="Three-pose test",icon="TIME")
        row=col.row(align=True)
        for frame,label in ((1,"A Hold"),(36,"B Crouch"),(72,"C Contact")):
            op=row.operator("fwai.jump_pose",text=label)
            op.frame=frame
        col.operator("fwai.select_rig",icon="BONE_DATA")
        col.operator("screen.animation_play",text="Play / Pause",icon="PLAY")
        col.operator("fwai.open_review",icon="FILE_FOLDER")
        col.separator()
        col.label(text="Rig/vehicle: visual proxies")
        col.label(text="Vinyl cloth: not baked")
        col.label(text="Creative QC: HOLD",icon="ERROR")
        col.label(text="Runway: disabled")
        col.label(text="Auto-delete: disabled")
classes=(FWAI_OT_jump_pose,FWAI_OT_open_review,FWAI_OT_select_rig,FWAI_PT_control)
def register():
    for cls in classes:bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes):bpy.utils.unregister_class(cls)
if __name__=="__main__":register()
