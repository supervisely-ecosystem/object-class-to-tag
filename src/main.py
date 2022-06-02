from typing import List

import debug_utils  # before import sly
import supervisely as sly

import globals as g


def map_class_names(src_meta: sly.ProjectMeta, result_class_name):
    shape2class = {}
    shape2geom_type = {}
    for c in src_meta.obj_classes:
        shape = c.geometry_type.geometry_name()
        shape2class[shape] = f'{result_class_name}_{shape}'
        shape2geom_type[shape] = c.geometry_type

    if len(shape2class) == 1:
        shape = next(iter(shape2class.keys()))
        shape2class = {shape: result_class_name}

    class_map = {c.name: shape2class[c.geometry_type.geometry_name()] for c in src_meta.obj_classes}

    return class_map, shape2class, shape2geom_type


def map_tag_names(src_meta: sly.ProjectMeta):
    res_tags = {c.name for c in src_meta.obj_classes}

    tag_map = {}
    for tag in src_meta.tag_metas:
        new_name = tag.name
        while new_name in res_tags:
            new_name += '_AUTO_RENAMED'
        tag_map[tag.name] = new_name
        res_tags.add(new_name)

    return tag_map


def create_new_classes(shape_to_class_name, shape_to_geom_type):
    def create_class(shape, cls_name):
        geom_type = shape_to_geom_type[shape]
        new_class = sly.ObjClass(name=cls_name, geometry_type=geom_type)
        return new_class

    new_classes = [create_class(shape, name) for shape, name in shape_to_class_name.items()]
    return sly.ObjClassCollection(new_classes)


def create_new_tags(src_meta: sly.ProjectMeta, tag_names_mapping):
    new_tags = []
    for tag in src_meta.tag_metas:
        new_tag = tag.clone(name=tag_names_mapping[tag.name])
        new_tags.append(new_tag)

    for cls in src_meta.obj_classes:
        new_tag = sly.TagMeta(name=cls.name,
                              value_type=sly.TagValueType.NONE,
                              applicable_to=sly.TagApplicableTo.OBJECTS_ONLY)
        new_tags.append(new_tag)

    return sly.TagMetaCollection(new_tags)


class AnnConvertor:
    def __init__(self, src_meta: sly.ProjectMeta, result_class_name: str):
        self.class_names_mapping, self.shape_to_class_name, self.shape_to_geom_type = \
            map_class_names(src_meta, result_class_name)

        self.tag_names_mapping = map_tag_names(src_meta)

        self._res_classes = create_new_classes(self.shape_to_class_name, self.shape_to_geom_type)
        self._res_tags = create_new_tags(src_meta, self.tag_names_mapping)
        self.res_meta = src_meta.clone(obj_classes=self._res_classes, tag_metas=self._res_tags)

    def convert(self, ann: sly.Annotation):
        res_labels = self._convert_labels(ann.labels)
        res_img_tags = self._convert_tags(ann.img_tags)
        res_ann = ann.clone(labels=res_labels, img_tags=res_img_tags)
        return res_ann

    def _convert_tags(self, tags: sly.TagCollection):
        return sly.TagCollection([self._convert_tag(t) for t in tags])

    def _convert_tag(self, tag: sly.Tag):
        new_tag_meta = self._res_tags.get(self.tag_names_mapping[tag.name])
        return tag.clone(meta=new_tag_meta)

    def _convert_labels(self, labels: List[sly.Label]):
        return [self._convert_label(lbl) for lbl in labels]

    def _convert_label(self, label: sly.Label):
        new_name = self.class_names_mapping[label.obj_class.name]
        new_cls = self._res_classes.get(new_name)
        new_tags = self._convert_tags(label.tags)

        new_tag_from_class = self._res_tags.get(label.obj_class.name)
        new_tags = new_tags.add(new_tag_from_class)
        return label.clone(obj_class=new_cls, tags=new_tags)


@sly.timeit
def classes_to_tags(api: sly.Api, result_class_name: str, result_project_name: str):
    meta_json = api.project.get_meta(g.PROJECT_ID)
    meta = sly.ProjectMeta.from_json(meta_json)

    convertor = AnnConvertor(meta, result_class_name)
    sly.logger.info(f'Mapping shape -> new class: {convertor.shape_to_class_name!s}')
    tag_renaming_to_log = {k: v for k, v in convertor.tag_names_mapping.items() if k != v}
    sly.logger.info(f'Renaming existing tags: {tag_renaming_to_log!s}')

    if not result_project_name:
        project_info = api.project.get_info_by_id(g.PROJECT_ID)
        result_project_name = f'{project_info.name} Tagged'

    res_project = api.project.create(g.WORKSPACE_ID, result_project_name,
                                     type=sly.ProjectType.IMAGES, change_name_if_conflict=True)
    api.project.update_meta(res_project.id, convertor.res_meta.to_json())

    datasets = api.dataset.get_list(g.PROJECT_ID)
    progress = sly.Progress('Processing annotations', sum(ds.items_count for ds in datasets))

    for dataset in datasets:
        res_dataset = api.dataset.create(res_project.id, dataset.name, change_name_if_conflict=True)
        img_infos = api.image.get_list(dataset.id)
        for img_infos_batch in sly.batched(img_infos):
            img_names, img_hashes, img_ids = zip(*((i.name, i.hash, i.id) for i in img_infos_batch))
            ann_jsons = api.annotation.download_batch(dataset.id, img_ids)

            anns = (sly.Annotation.from_json(ann_json.annotation, meta) for ann_json in ann_jsons)
            res_anns = [convertor.convert(ann) for ann in anns]

            new_img_infos = api.image.upload_hashes(res_dataset.id, names=img_names, hashes=img_hashes)
            api.annotation.upload_anns([i.id for i in new_img_infos], res_anns)

            progress.iters_done_report(len(img_infos_batch))

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
