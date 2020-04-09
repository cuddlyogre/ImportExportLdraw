bl_info = {
    "name": "Export LDraw",
    "author": "cuddlyogre",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "File > Export > LDraw (.mpd/.ldr/.l3b/.dat)",
    "description": "Imports and Exports LDraw Models",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib

    importlib.reload(options)
    importlib.reload(face_info)
    importlib.reload(filesystem)
    importlib.reload(helpers)
    importlib.reload(ldraw_export)
    importlib.reload(ldraw_file)
    importlib.reload(ldraw_node)
    importlib.reload(ldraw_geometry)
    importlib.reload(ldraw_import)
    importlib.reload(ldraw_colors)
    importlib.reload(ldraw_camera)
    importlib.reload(ldraw_part_types)
    importlib.reload(blender_materials)
    importlib.reload(matrices)
    importlib.reload(special_bricks)
else:
    from . import options
    from . import face_info
    from . import filesystem
    from . import helpers
    from . import ldraw_export
    from . import ldraw_file
    from . import ldraw_node
    from . import ldraw_geometry
    from . import ldraw_import
    from . import ldraw_colors
    from . import ldraw_camera
    from . import ldraw_part_types
    from . import blender_materials
    from . import matrices
    from . import special_bricks

import time
import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper


class IMPORT_OT_do_ldraw_import(bpy.types.Operator, ImportHelper):
    bl_idname = "import.ldraw"
    bl_label = "Import LDraw"
    bl_options = {'PRESET'}
    filename_ext = ""

    filter_glob: bpy.props.StringProperty(
        default="*.mpd;*.ldr;*.l3b;*.dat",
        options={'HIDDEN'},
    )

    ldraw_path: bpy.props.StringProperty(
        name="",
        description="Full filepath to the LDraw Parts Library (download from http://www.ldraw.org)",
        default=filesystem.locate_ldraw()
    )

    use_alt_colors: bpy.props.BoolProperty(
        name="Use alternate colors",
        description="Use LDCfgalt.ldr",
        default=True,
    )

    remove_doubles: bpy.props.BoolProperty(
        name="Remove doubles",
        description="Merge overlapping verices",
        default=True,
    )

    merge_distance: bpy.props.FloatProperty(
        name="Merge Distance",
        description="Maximum distance between elements to merge",
        default=0.05,
        precision=3,
        min=0.0,
    )

    shade_smooth: bpy.props.BoolProperty(
        name="Shade smooth",
        description="Shade smooth",
        default=True,
    )

    add_subsurface: bpy.props.BoolProperty(
        name="Add subsurface",
        description="Add subsurface to materials",
        default=True,
    )

    bevel_edges: bpy.props.BoolProperty(
        name="Bevel edges",
        description="Add bevel to edges",
        default=False,
    )

    resolution: bpy.props.EnumProperty(
        name="Part resolution",
        description="Resolution of part primitives, ie. how much geometry they have",
        default="Standard",
        items=(
            ("Low", "Low resolution primitives", "Import using low resolution primitives."),
            ("Standard", "Standard primitives", "Import using standard resolution primitives."),
            ("High", "High resolution primitives", "Import using high resolution primitives."),
        )
    )

    display_logo: bpy.props.BoolProperty(
        name="Display logo",
        description="Display logo on studs. Requires unofficial parts library to be downloaded",
        default=False
    )

    chosen_logo: bpy.props.EnumProperty(
        name="Chosen logo",
        description="Use this logo on studs",
        default=special_bricks.logos[2],
        items=((l, l, l) for l in special_bricks.logos)
    )

    smooth_type: bpy.props.EnumProperty(
        name="Smooth type",
        description="Use this strategy to smooth meshes",
        default="auto_smooth",
        items=(
            ("auto_smooth", "Auto smooth", "Use auto smooth"),
            ("edge_split", "Edge split", "Use an edge split modifier"),
        )
    )

    gap_target: bpy.props.EnumProperty(
        name="Gap target",
        description="Where to apply gap",
        default="object",
        items=(
            ("object", "Object", "Scale the object to create the gap"),
            ("mesh", "Mesh", "Transform the mesh to create the gap"),
        )
    )

    gap_scale_strategy: bpy.props.EnumProperty(
        name="Gap strategy",
        description="How to scale the object to create the gap",
        default="constraint",
        items=(
            ("object", "Object", "Apply gap directly to the object"),
            ("constraint", "Constraint", "Use a constraint, allowing the gap to easily be adjusted later"),
        )
    )

    debug_text: bpy.props.BoolProperty(
        name="Debug text",
        description="Show debug text. Negatively affects performance",
        default=False
    )

    no_studs: bpy.props.BoolProperty(
        name="No studs",
        description="Don't import studs",
        default=False
    )

    parent_to_empty: bpy.props.BoolProperty(
        name="Parent to empty",
        description="Parent the model to an empty",
        default=True
    )

    import_scale: bpy.props.FloatProperty(
        name="Import scale",
        description="Scale the entire model by this amount",
        default=0.02,
        precision=2,
        min=0.01,
        max=1.00,
    )

    make_gaps: bpy.props.BoolProperty(
        name="Make gaps",
        description="Puts small gaps between parts",
        default=True
    )

    gap_scale: bpy.props.FloatProperty(
        name="Gap scale",
        description="Scale parts by this value to make gaps",
        default=0.997,
        precision=3,
        min=0.0,
        max=1.0,
    )

    meta_print_write: bpy.props.BoolProperty(
        name="PRINT/WRITE",
        description="Process PRINT/WRITE meta command",
        default=False
    )

    meta_group: bpy.props.BoolProperty(
        name="GROUP",
        description="Process GROUP meta commands",
        default=True
    )

    meta_step: bpy.props.BoolProperty(
        name="STEP",
        description="Process STEP meta command",
        default=False
    )

    meta_clear: bpy.props.BoolProperty(
        name="CLEAR",
        description="Process CLEAR meta command",
        default=False
    )

    meta_pause: bpy.props.BoolProperty(
        name="PAUSE",
        description="Process PAUSE meta command",
        default=False
    )

    meta_save: bpy.props.BoolProperty(
        name="SAVE",
        description="Process SAVE meta command",
        default=False
    )

    set_end_frame: bpy.props.BoolProperty(
        name="Set step end frame",
        description="Set the end frame to the last step",
        default=False
    )

    frames_per_step: bpy.props.IntProperty(
        name="Frames per step",
        description="Frames per step",
        default=3,
        min=1,
    )

    set_timelime_markers: bpy.props.BoolProperty(
        name="Set timeline markers",
        description="Set timeline markers for meta commands",
        default=False
    )

    import_edges: bpy.props.BoolProperty(
        name="Import edges",
        description="Import edge meshes",
        default=False
    )

    grease_pencil_edges: bpy.props.BoolProperty(
        name="Imported edges as grease pencil",
        description="Import edges as grease pencil strokes",
        default=False
    )

    all_materials: bpy.props.BoolProperty(
        name="Import all materials",
        description="Import all materials from chosen LDConfig.ldr file",
        default=False
    )

    prefer_unofficial: bpy.props.BoolProperty(
        name="Prefer unofficial parts",
        description="Search for unofficial parts first",
        default=False
    )

    recalculate_normals: bpy.props.BoolProperty(
        name="Recalculate normals",
        description="Recalculate normals",
        default=True
    )

    def execute(self, context):
        start = time.monotonic()

        options.ldraw_path = self.ldraw_path
        options.resolution = self.resolution
        options.use_alt_colors = self.use_alt_colors
        options.remove_doubles = self.remove_doubles
        options.merge_distance = self.merge_distance
        options.shade_smooth = self.shade_smooth
        options.display_logo = self.display_logo
        options.chosen_logo = self.chosen_logo
        options.make_gaps = self.make_gaps
        options.gap_scale = self.gap_scale
        options.debug_text = self.debug_text
        options.no_studs = self.no_studs
        options.bevel_edges = self.bevel_edges
        options.set_timelime_markers = self.set_timelime_markers
        options.meta_group = self.meta_group
        options.meta_print_write = self.meta_print_write
        options.meta_step = self.meta_step
        options.meta_clear = self.meta_clear
        options.meta_pause = self.meta_pause
        options.meta_save = self.meta_save
        options.set_end_frame = self.set_end_frame
        options.frames_per_step = self.frames_per_step
        options.add_subsurface = self.add_subsurface
        options.smooth_type = self.smooth_type
        options.import_edges = self.import_edges
        options.grease_pencil_edges = self.grease_pencil_edges
        options.import_scale = self.import_scale
        options.parent_to_empty = self.parent_to_empty
        options.gap_target = self.gap_target
        options.gap_scale_strategy = self.gap_scale_strategy
        options.prefer_unofficial = self.prefer_unofficial
        options.all_materials = self.all_materials
        options.recalculate_normals = self.recalculate_normals

        ldraw_import.do_import(bpy.path.abspath(self.filepath))

        print("")
        print("======Import Complete======")
        print(self.filepath)
        print(f"Part count: {ldraw_node.part_count}")
        end = time.monotonic()
        elapsed = (end - start)
        print(f"elapsed: {elapsed}")
        print("===========================")
        print("")

        return {'FINISHED'}

    # https://docs.blender.org/api/current/bpy.types.UILayout.html
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        box = layout.box()

        box.label(text="LDraw filepath:", icon='FILEBROWSER')
        box.prop(self, "ldraw_path")

        box.label(text="Import Options")
        box.prop(self, "use_alt_colors")
        box.prop(self, "resolution", expand=True)
        box.prop(self, "display_logo")
        box.prop(self, "chosen_logo")

        box.label(text="Scaling Options")
        box.prop(self, "import_scale")
        box.prop(self, "parent_to_empty")
        box.prop(self, "make_gaps")
        box.prop(self, "gap_scale")
        box.prop(self, "gap_target")
        box.prop(self, "gap_scale_strategy")

        box.label(text="Cleanup Options")
        box.prop(self, "remove_doubles")
        box.prop(self, "merge_distance")
        box.prop(self, "smooth_type")
        box.prop(self, "shade_smooth")
        box.prop(self, "recalculate_normals")

        box.label(text="Meta Commands")
        box.prop(self, "meta_group")
        box.prop(self, "meta_print_write")
        box.prop(self, "meta_step")
        box.prop(self, "frames_per_step")
        box.prop(self, "set_end_frame")
        box.prop(self, "meta_clear")
        # box.prop(self, "meta_pause")
        box.prop(self, "meta_save")
        box.prop(self, "set_timelime_markers")

        box.label(text="Extras")
        box.prop(self, "prefer_unofficial")
        box.prop(self, "all_materials")
        box.prop(self, "add_subsurface")
        box.prop(self, "bevel_edges")
        box.prop(self, "debug_text")
        box.prop(self, "no_studs")
        box.prop(self, "import_edges")
        box.prop(self, "grease_pencil_edges")


class EXPORT_OT_do_ldraw_export(bpy.types.Operator, ExportHelper):
    bl_idname = "export.ldraw"
    bl_label = "Export LDraw"
    bl_options = {'PRESET'}
    filename_ext = ""

    filter_glob: bpy.props.StringProperty(
        default="*.mpd;*.ldr;*.l3b;*.dat",
        options={'HIDDEN'},
    )

    ldraw_path: bpy.props.StringProperty(
        name="",
        description="Full filepath to the LDraw Parts Library (download from http://www.ldraw.org)",
        default=filesystem.locate_ldraw()
    )

    use_alt_colors: bpy.props.BoolProperty(
        name="Use alternate colors",
        description="Use LDCfgalt.ldr",
        default=True,
    )

    selection_only: bpy.props.BoolProperty(
        name="Selection only",
        description="Export selected objects only",
        default=True
    )

    recalculate_normals: bpy.props.BoolProperty(
        name="Recalculate normals",
        description="Recalculate normals",
        default=True
    )

    triangulate: bpy.props.BoolProperty(
        name="Triangulate mesh",
        description="Triangulate the entire mesh",
        default=False
    )

    remove_doubles: bpy.props.BoolProperty(
        name="Remove doubles",
        description="Merge overlapping verices",
        default=True,
    )

    merge_distance: bpy.props.FloatProperty(
        name="Merge Distance",
        description="Maximum distance between elements to merge",
        default=0.05,
        precision=3,
        min=0.0,
    )

    ngon_handling: bpy.props.EnumProperty(
        name="Ngon handling",
        description="What to do with ngons",
        items=[
            ("skip", "Skip", "Don't export ngons at all"),
            ("triangulate", "Triangulate", "Triangulate ngons"),
        ],
        default="triangulate",
    )

    export_precision: bpy.props.IntProperty(
        name="Export precision",
        description="Round vertex coordinates to this number of places",
        default=2,
        min=0,
    )

    def execute(self, context):
        start = time.monotonic()

        options.ldraw_path = self.ldraw_path
        options.use_alt_colors = self.use_alt_colors
        options.selection_only = self.selection_only
        options.export_precision = self.export_precision
        options.remove_doubles = self.remove_doubles
        options.merge_distance = self.merge_distance
        options.recalculate_normals = self.recalculate_normals
        options.triangulate = self.triangulate
        options.ngon_handling = self.ngon_handling

        ldraw_export.do_export(bpy.path.abspath(self.filepath))

        print("")
        print("======Export Complete======")
        print(self.filepath)
        end = time.monotonic()
        elapsed = (end - start)
        print(f"elapsed: {elapsed}")
        print("===========================")
        print("")

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        box = layout.box()

        box.label(text="LDraw filepath:", icon='FILEBROWSER')
        box.prop(self, "ldraw_path")

        box.label(text="Export Options")
        box.prop(self, "selection_only")
        box.prop(self, "use_alt_colors")
        box.prop(self, "export_precision")

        box.label(text="Cleanup Options")
        box.prop(self, "remove_doubles")
        box.prop(self, "merge_distance")
        box.prop(self, "recalculate_normals")
        box.prop(self, "triangulate")
        box.prop(self, "ngon_handling")


def build_import_menu(self, context):
    self.layout.operator(IMPORT_OT_do_ldraw_import.bl_idname, text="Basic LDraw (.mpd/.ldr/.l3b/.dat)")


def build_export_menu(self, context):
    self.layout.operator(EXPORT_OT_do_ldraw_export.bl_idname, text="LDraw (.mpd/.ldr/.l3b/.dat)")


def register():
    bpy.utils.register_class(IMPORT_OT_do_ldraw_import)
    bpy.types.TOPBAR_MT_file_import.append(build_import_menu)

    bpy.utils.register_class(EXPORT_OT_do_ldraw_export)
    bpy.types.TOPBAR_MT_file_export.append(build_export_menu)


def unregister():
    bpy.utils.unregister_class(IMPORT_OT_do_ldraw_import)
    bpy.types.TOPBAR_MT_file_import.remove(build_import_menu)

    bpy.utils.unregister_class(EXPORT_OT_do_ldraw_export)
    bpy.types.TOPBAR_MT_file_export.remove(build_export_menu)


if __name__ == "__main__":
    register()
