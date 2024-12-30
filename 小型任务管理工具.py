import json
from datetime import datetime

import flet as ft

# 数据存储文件
DATA_FILE = "projects.json"


# 加载数据
def load_data():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# 保存数据
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


# 主应用程序
def main(page: ft.Page):
    page.title = "项目任务管理(0.1)-Mr.Lee"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    # 加载项目数据
    projects = load_data()

    # 左侧项目列表
    project_list = ft.ListView(expand=True, spacing=10)

    # 右侧任务树状图
    task_tree = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    # 当前选中的项目
    current_project = None

    # 当前项目名称显示控件
    current_project_display = ft.Text("", size=16, color=ft.colors.BLUE)

    # 添加项目按钮
    def add_project(e):
        new_project_name = new_project_input.value.strip()
        if new_project_name:
            if new_project_name in projects:
                page.overlay.append(ft.SnackBar(ft.Text("项目名称已存在，请使用其他名称！"), open=True))
            else:
                projects[new_project_name] = {"tasks": {}}
                save_data(projects)
                update_project_list()
                new_project_input.value = ""
            page.overlay.append(ft.SnackBar(ft.Text("项目添加成功！"), open=True))
        else:
            page.overlay.append(ft.SnackBar(ft.Text("项目名称不能为空！"), open=True))
        page.update()

    new_project_input = ft.TextField(
        hint_text="输入项目名称",
        label="项目名称",
        expand=True,
        border_radius=ft.BorderRadius(top_left=3, top_right=0, bottom_left=3, bottom_right=0)
    )
    add_project_button = ft.IconButton(
        on_click=add_project,
        icon=ft.icons.FORMAT_LIST_BULLETED_ADD,
        style=ft.ButtonStyle(
            shape=ft.BeveledRectangleBorder(radius=0),
            side=ft.BorderSide(width=0.3)
        ),
        height=48
    )

    # 更新项目列表
    def update_project_list():
        project_list.controls.clear()
        for idx, project_name in enumerate(projects.keys(), start=1):
            project_item = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.icons.CONTENT_PASTE_OUTLINED, size=16),
                                ft.Text(f"{idx}. {project_name}", size=16),
                            ]),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    on_click=lambda e, name=project_name: edit_project_name(name),
                                    icon_size=16
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e, name=project_name: delete_project(name),
                                    icon_size=16
                                ),
                            ]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                on_click=lambda e, name=project_name: select_project(e, name),
                padding=10,
                border_radius=5,
            )
            project_list.controls.append(project_item)
        page.update()

    # 修改项目名称
    def edit_project_name(project_name):
        new_name_input = ft.TextField(hint_text="输入新项目名称", value=project_name)
        dialog = ft.AlertDialog(
            title=ft.Text("修改项目名称"),
            content=new_name_input,
            actions=[
                ft.ElevatedButton(
                    "保存",
                    on_click=lambda e: save_project_name(project_name, new_name_input.value),
                ),
                ft.ElevatedButton("取消", on_click=lambda e: close_dialog(dialog)),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def save_project_name(old_name, new_name):
        if new_name:
            if new_name in projects:
                page.overlay.append(ft.SnackBar(ft.Text("项目名称已存在，请使用其他名称！"), open=True))
            else:
                projects[new_name] = projects.pop(old_name)
                save_data(projects)
                update_project_list()
                if current_project == old_name:
                    select_project(None, new_name)
                page.overlay.append(ft.SnackBar(ft.Text("项目名称修改成功！"), open=True))
                close_dialog()
        else:
            page.overlay.append(ft.SnackBar(ft.Text("项目名称不能为空！"), open=True))
        page.update()

    # 删除项目
    def delete_project(project_name):
        del projects[project_name]
        save_data(projects)
        update_project_list()
        if current_project == project_name:
            task_tree.controls.clear()
            current_project_display.value = ""
            page.overlay.append(ft.SnackBar(ft.Text(f"项目 {project_name} 已删除！"), open=True))
        page.update()

    # 选择项目
    def select_project(e, project_name):
        # 恢复所有项目项的默认背景色
        for item in project_list.controls:
            if isinstance(item, ft.Container):  # 确保是项目项
                item.bgcolor = None
        # 设置当前项目项的背景色为浅蓝色
        if e:
            e.control.bgcolor = ft.colors.BLUE_100
        # 更新当前项目名称显示
        current_project_display.value = project_name
        # 显示任务
        show_tasks(project_name)
        page.update()

    # 显示任务
    def show_tasks(project_name):
        nonlocal current_project
        current_project = project_name
        task_tree.controls.clear()
        for task_id, task_data in projects[project_name]["tasks"].items():
            # 如果是根任务，直接添加
            if task_id.startswith("root."):
                task_tree.controls.append(
                    build_task_item(project_name, task_id, task_data, indent_level=0)
                )
                # 添加子任务
                if "subtasks" in task_data:
                    for subtask_id, subtask_data in task_data["subtasks"].items():
                        task_tree.controls.append(
                            build_task_item(project_name, subtask_id, subtask_data, indent_level=1, sub=True)
                        )
        page.update()

    # 高亮任务项
    def highlight_task_item(e, task_item):
        # 恢复所有任务项的默认背景色
        for item in task_tree.controls:
            if isinstance(item, ft.Container):  # 确保是任务项
                item.bgcolor = None
        # 设置当前任务项的背景色为浅蓝色
        task_item.bgcolor = ft.colors.BLUE_100
        page.update()

    # 构建任务项
    def build_task_item(project_name, task_id, task_data, indent_level, sub=False):
        task_name = task_data["name"]
        completed = task_data.get("completed", False)
        completed_time = task_data.get("completed_time", "")
        created_time = task_data.get("created_time", "")
        note = task_data.get("note", "")

        # 任务名称输入框
        task_name_input = ft.TextField(
            label="任务名称",
            value=task_name,
            border_radius=ft.BorderRadius(top_left=3, top_right=0, bottom_left=3, bottom_right=0)
        )

        # 任务备注输入框
        note_input = ft.TextField(label="备注", multiline=True, value=note)

        # 自动保存备注的函数
        def save_note(e):
            if "." in task_id and task_id.count(".") > 1:  # 子任务
                parent_task_id = task_id[:task_id.rfind(".")]
                if parent_task_id in projects[project_name]["tasks"]:
                    projects[project_name]["tasks"][parent_task_id]["subtasks"][task_id]["note"] = note_input.value
                else:
                    # 如果父任务不存在，可能是根任务的子任务
                    for root_task_id, root_task_data in projects[project_name]["tasks"].items():
                        if task_id.startswith(root_task_id):
                            root_task_data["subtasks"][task_id]["note"] = note_input.value
                            break
            else:  # 根任务
                projects[project_name]["tasks"][task_id]["note"] = note_input.value
            save_data(projects)
            # 显示保存成功的提示
            page.overlay.append(ft.SnackBar(ft.Text("备注已保存！"), open=True))
            page.update()

        # 绑定输入框的 on_change 事件
        note_input.on_change = save_note

        # 任务详情
        task_details = ft.Column(
            controls=[
                ft.Text(f"添加日期: {created_time}", size=16),
                ft.Text(f"完成日期: {completed_time}", size=16),
                ft.Row(
                    controls=[
                        task_name_input,
                        ft.IconButton(
                            on_click=lambda e: save_task_name(project_name, task_id, task_name_input.value),
                            icon=ft.icons.CHECK,
                            style=ft.ButtonStyle(
                                shape=ft.BeveledRectangleBorder(radius=0),
                                side=ft.BorderSide(width=0.3)
                            ),
                            height=48
                        )
                    ],
                    spacing=0
                ),  # 任务名称输入框
                note_input,
            ],
            visible=False,
        )

        # 生成任务编号
        if sub:
            # 子任务编号
            parts = task_id.split(".")
            task_number = ".".join(parts[1:])  # 去掉 "root" 部分
        else:
            # 根任务编号
            task_number = task_id.split(".")[1]

        # 任务项
        task_item = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(" " * 8 * indent_level + f"{task_number}. {task_name}", size=20),
                            ft.Text("已完成" if completed else "未完成", size=16, color="blue" if completed else "red"),
                            ft.IconButton(
                                ft.icons.TASK_ALT,
                                on_click=lambda e: [complete_task(project_name, task_id), highlight_task_item(e, task_item)],
                                icon_size=16
                            ),
                            ft.IconButton(
                                ft.icons.CLEAR,
                                on_click=lambda e: [uncomplete_task(project_name, task_id), highlight_task_item(e, task_item)],
                                icon_size=16
                            ),
                            ft.IconButton(
                                ft.icons.ADD,
                                on_click=lambda e: [add_subtask(project_name, task_id), highlight_task_item(e, task_item)],
                                icon_size=16
                            ),
                            ft.IconButton(
                                ft.icons.DELETE,
                                on_click=lambda e: [delete_task(project_name, task_id), highlight_task_item(e, task_item)],
                                icon_size=16
                            ),
                            ft.IconButton(
                                icon=ft.icons.EXPAND_MORE,
                                on_click=lambda e: [toggle_task_details(e, task_details), highlight_task_item(e, task_item)],
                            ),
                        ],
                    ),
                    task_details,
                ],
            ),
            # 添加点击事件
            on_click=lambda e: highlight_task_item(e, task_item),
            padding=10,  # 添加内边距
            border_radius=5,  # 添加圆角
        )
        if sub:
            task_item.content.controls[0].controls.pop(4)
        return task_item

    # 保存任务名称
    def save_task_name(project_name, task_id, new_name):
        if "." in task_id and task_id.count(".") > 1:  # 子任务
            parent_task_id = task_id[:task_id.rfind(".")]
            if parent_task_id in projects[project_name]["tasks"]:
                projects[project_name]["tasks"][parent_task_id]["subtasks"][task_id]["name"] = new_name
            else:
                # 如果父任务不存在，可能是根任务的子任务
                for root_task_id, root_task_data in projects[project_name]["tasks"].items():
                    if task_id.startswith(root_task_id):
                        root_task_data["subtasks"][task_id]["name"] = new_name
                        break
        else:  # 根任务
            projects[project_name]["tasks"][task_id]["name"] = new_name
        save_data(projects)
        show_tasks(project_name)

    # 切换任务详情
    def toggle_task_details(e, task_details):
        task_details.visible = not task_details.visible
        page.update()

    # 完成任务
    def complete_task(project_name, task_id):
        if "." in task_id and task_id.count(".") > 1:  # 子任务
            parent_task_id = task_id[:task_id.rfind(".")]
            if parent_task_id in projects[project_name]["tasks"]:
                projects[project_name]["tasks"][parent_task_id]["subtasks"][task_id]["completed"] = True
                projects[project_name]["tasks"][parent_task_id]["subtasks"][task_id]["completed_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                # 如果父任务不存在，可能是根任务的子任务
                for root_task_id, root_task_data in projects[project_name]["tasks"].items():
                    if task_id.startswith(root_task_id):
                        root_task_data["subtasks"][task_id]["completed"] = True
                        root_task_data["subtasks"][task_id]["completed_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        break
        else:  # 根任务
            projects[project_name]["tasks"][task_id]["completed"] = True
            projects[project_name]["tasks"][task_id]["completed_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_data(projects)
        show_tasks(project_name)

    # 未完成任务
    def uncomplete_task(project_name, task_id):
        if "." in task_id and task_id.count(".") > 1:  # 子任务
            parent_task_id = task_id[:task_id.rfind(".")]
            if parent_task_id in projects[project_name]["tasks"]:
                projects[project_name]["tasks"][parent_task_id]["subtasks"][task_id]["completed"] = False
                projects[project_name]["tasks"][parent_task_id]["subtasks"][task_id]["completed_time"] = ""
            else:
                # 如果父任务不存在，可能是根任务的子任务
                for root_task_id, root_task_data in projects[project_name]["tasks"].items():
                    if task_id.startswith(root_task_id):
                        root_task_data["subtasks"][task_id]["completed"] = False
                        root_task_data["subtasks"][task_id]["completed_time"] = ""
                        break
        else:  # 根任务
            projects[project_name]["tasks"][task_id]["completed"] = False
            projects[project_name]["tasks"][task_id]["completed_time"] = ""
        save_data(projects)
        show_tasks(project_name)

    # 添加子任务
    def add_subtask(project_name, parent_task_id):
        new_subtask_name = ft.TextField(hint_text="输入子任务名称")
        dialog = ft.AlertDialog(
            title=ft.Text("添加子任务"),
            content=new_subtask_name,
            actions=[
                ft.ElevatedButton(
                    "添加",
                    on_click=lambda e: save_subtask(project_name, parent_task_id, new_subtask_name.value),
                ),
                ft.ElevatedButton("取消", on_click=lambda e: close_dialog(dialog)),
            ],
        )
        page.overlay.append(dialog)  # Add dialog to overlay
        dialog.open = True
        page.update()

    def save_subtask(project_name, parent_task_id, subtask_name):
        if subtask_name:
            # 获取父任务对象
            if "." in parent_task_id:  # 如果父任务是子任务
                # 递归查找父任务
                parts = parent_task_id.split(".")
                current_task = projects[project_name]["tasks"][f"{parts[0]}.{parts[1]}"]  # 根任务
                for part in parts[2:]:
                    current_task = current_task["subtasks"][f"{'.'.join(parts[:parts.index(part) + 1])}"]
            else:  # 如果父任务是根任务
                current_task = projects[project_name]["tasks"][parent_task_id]

            # 初始化父任务的 subtasks 字段
            if "subtasks" not in current_task:
                current_task["subtasks"] = {}

            # 生成唯一的子任务 ID
            subtask_id = f"{parent_task_id}.{len(current_task['subtasks']) + 1}"

            # 创建子任务数据
            subtask_data = {
                "name": subtask_name,
                "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "completed": False,
                "completed_time": "",
                "note": "",
                "subtasks": {},  # 初始化子任务
            }

            # 将子任务添加到父任务的 subtasks 字段中
            current_task["subtasks"][subtask_id] = subtask_data

            # 保存数据并更新界面
            save_data(projects)
            show_tasks(project_name)
            close_dialog()

    # 添加根任务
    def add_root_task(e):
        if current_project:
            new_task_name = ft.TextField(hint_text="输入根任务名称")
            dialog = ft.AlertDialog(
                title=ft.Text("添加根任务"),
                content=new_task_name,
                actions=[
                    ft.ElevatedButton(
                        "添加",
                        on_click=lambda e: save_root_task(current_project, new_task_name.value),
                    ),
                    ft.ElevatedButton("取消", on_click=lambda e: close_dialog(dialog)),
                ],
            )
            page.overlay.append(dialog)  # Add dialog to overlay
            dialog.open = True
        else:
            page.overlay.append(ft.SnackBar(ft.Text("请新建或者选择项目！"), open=True))
        page.update()

    def save_root_task(project_name, task_name):
        if task_name:
            task_id = f"root.{len(projects[project_name]['tasks']) + 1}"
            projects[project_name]["tasks"][task_id] = {
                "name": task_name,
                "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "completed": False,
                "completed_time": "",
                "note": "",
                "subtasks": {},  # 初始化子任务
            }
            save_data(projects)
            show_tasks(project_name)
            close_dialog()

    def close_dialog(dialog):
        if dialog in page.overlay:  # Check if dialog is in overlay
            page.close(dialog)  # Remove dialog from overlay
            page.update()

    # 删除任务
    def delete_task(project_name, task_id):
        if "." in task_id and task_id.count(".") > 1:  # 子任务
            parent_task_id = task_id[:task_id.rfind(".")]
            if parent_task_id in projects[project_name]["tasks"]:
                del projects[project_name]["tasks"][parent_task_id]["subtasks"][task_id]
            else:
                # 如果父任务不存在，可能是根任务的子任务
                for root_task_id, root_task_data in projects[project_name]["tasks"].items():
                    if task_id.startswith(root_task_id):
                        del root_task_data["subtasks"][task_id]
                        break
        else:  # 根任务
            del projects[project_name]["tasks"][task_id]
        save_data(projects)
        show_tasks(project_name)

    # 初始化项目列表
    update_project_list()

    # 布局
    page.add(
        ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("项目列表", size=20),
                        ft.Row(controls=[new_project_input, add_project_button], spacing=0),
                        project_list,
                    ],
                    width=300,
                ),
                ft.VerticalDivider(width=10),
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("任务分解", size=20),
                                current_project_display,  # 显示当前项目名称
                                ft.IconButton(ft.icons.NOTE_ADD_OUTLINED, on_click=add_root_task),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        task_tree,
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        )
    )


# 运行应用程序
ft.app(target=main)
