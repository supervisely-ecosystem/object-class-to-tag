import sys

if '--DebugImportEnvsFromFiles' in sys.argv:
    import debug_utils
    debug_utils.load_envs_from_files()

import supervisely as sly

import globals as g


# def create_mappings(src_project_meta, result_class_name):
#     class_shapes = set(c.shape for c in src_project_meta.obj_classes)
#     source_tags = set(t.name for t in src_project_meta.tag_metas)
#     for


def map_object_class_names(src_meta, result_class_name) -> dict[str, str]:
    def shape_name(obj_cls):
        return obj_cls.geometry_type.geometry_name()

    shape2class = {shape_name(c): f'{result_class_name}_{shape_name(c)}' for c in src_meta.obj_classes}
    if len(shape2class) == 1:
        shape = next(iter(shape2class.keys()))
        shape2class = {shape: result_class_name}
    return shape2class


def map_tag_names(src_meta) -> dict[str, str]:
    res_tags = {c.name for c in src_meta.obj_classes}
    tag_map = {}
    for tag in src_meta.tag_metas:
        new_name = tag.name
        while new_name in res_tags:
            new_name += '_AUTO_RENAMED'
        tag_map[tag.name] = new_name
        res_tags.add(new_name)
    return tag_map


@sly.timeit
def classes_to_tags(api: sly.Api, result_class_name: str, result_project_name: str):
    if not result_project_name:
        project_info = api.project.get_info_by_id(g.PROJECT_ID)
        result_project_name = f'{project_info.name} Tagged'

    meta_json = api.project.get_meta(g.PROJECT_ID)
    meta = sly.ProjectMeta.from_json(meta_json)

    shape_to_class_name = map_object_class_names(meta, result_class_name)
    sly.logger.info(f'Mapping shape -> new class: {shape_to_class_name!s}')

    tag_names_mapping = map_tag_names(meta)
    tag_renaming_to_log = {k: v for k, v in tag_names_mapping.items() if k != v}
    sly.logger.info(f'Renaming existing tags: {tag_renaming_to_log!s}')



    sly.logger.debug('Finished classes_to_tags')


if __name__ == '__main__':
    sly.logger.info(
        'Script arguments',
        extra={
            'context.teamId': g.TEAM_ID,
            'context.workspaceId': g.WORKSPACE_ID,
            'modal.state.slyProjectId': g.PROJECT_ID,
            'modal.state.resultClassName': g.RES_CLASS_NAME,
            'modal.state.resultProjectName': g.RES_PROJECT_NAME
        },
    )

    classes_to_tags(g.api, g.RES_CLASS_NAME, g.RES_PROJECT_NAME)

    try:
        sly.app.fastapi.shutdown()
    except KeyboardInterrupt:
        sly.logger.info('Application shutdown successfully')
