"""Interfaz Streamlit de la ToDo App.

La persistencia es exclusivamente st.session_state: al reiniciar la app la
lista arranca vacía. No hay base de datos, archivos ni st.cache_resource.

Patrón de actualización: todas las acciones (agregar / toggle / guardar /
eliminar) se ejecutan en callbacks (on_change / on_click), que Streamlit
invoca ANTES de re-renderizar el script. Así el estado de TodoList ya está
actualizado cuando se vuelve a dibujar la lista y nunca se muta mientras se
itera sobre la vista anterior. No se usa st.experimental_rerun (deprecado).
"""

from __future__ import annotations

import streamlit as st

from todo_service import TodoList, Task

# Claves de sesión utilizadas.
TODO_LIST_KEY = "todo_list"

# Etiquetas visibles del filtro -> valores aceptados por list_tasks().
FILTER_OPTIONS: dict[str, str] = {
    "Todas": "all",
    "Pendientes": "pending",
    "Completadas": "completed",
}


def _get_todo_list() -> TodoList:
    """Devuelve la única instancia de TodoList guardada en la sesión,
    creándola solo si aún no existe."""
    if TODO_LIST_KEY not in st.session_state:
        st.session_state[TODO_LIST_KEY] = TodoList()
    return st.session_state[TODO_LIST_KEY]


# ---------------------------------------------------------------------------
# Callbacks (se ejecutan antes del siguiente re-render del script)
# ---------------------------------------------------------------------------

def _add_task() -> None:
    """Callback del formulario de alta: agrega la tarea o registra el error.

    Al ejecutarse ANTES de instanciar los widgets del run actual, puede
    asignar el estado del input para limpiarlo tras un alta exitosa. Si el
    título es inválido NO se crea nada y se conserva el texto para que la
    persona pueda corregirlo.
    """
    todo_list = _get_todo_list()
    new_title = st.session_state.get("todo_new_title", "")
    try:
        todo_list.add(new_title)
    except ValueError as exc:
        st.session_state["add_error"] = f"No se pudo agregar la tarea: {exc}"
    else:
        st.session_state["todo_new_title"] = ""


def _toggle_task(task_id: str) -> None:
    """Callback del checkbox: alterna completado/pendiente de la tarea."""
    _get_todo_list().toggle(task_id)


def _update_task(task_id: str) -> None:
    """Callback del botón Guardar: renombra la tarea con el texto actual
    del input. Si el título es inválido se muestra un error y la tarea NO
    se modifica; además se revierte el input a su título vigente.

    En ambos casos (éxito o error) se elimina la clave del widget tras
    procesarlo: como el callback corre antes de instanciar el input en
    este re-render, el widget se reinicializa desde value=task.title y
    queda sincronizado con el título almacenado (ya normalizado con
    strip()).
    """
    new_title = st.session_state.get(f"title_{task_id}", "")
    try:
        _get_todo_list().update(task_id, new_title)
    except KeyError:
        pass  # La tarea ya no existe: nada que guardar.
    except ValueError as exc:
        st.session_state[f"update_error_{task_id}"] = f"No se pudo guardar: {exc}"
    finally:
        # Sincroniza el input con el título vigente (sea el nuevo o el
        # anterior, si el guardado falló por título inválido).
        st.session_state.pop(f"title_{task_id}", None)


def _delete_task(task_id: str) -> None:
    """Callback del botón Eliminar: borra la tarea por id."""
    try:
        _get_todo_list().delete(task_id)
    except KeyError:
        pass  # La tarea ya no existe (interacción repetida): nada que hacer.


# ---------------------------------------------------------------------------
# Render de una tarea individual
# ---------------------------------------------------------------------------

def _render_task(task: Task) -> None:
    """Dibuja los controles de UNA tarea. No muta el estado de la lista."""
    with st.container(border=True):
        st.checkbox(
            "Completada",
            value=task.done,
            key=f"done_{task.id}",
            on_change=_toggle_task,
            args=(task.id,),
        )

        col_title, col_save, col_delete = st.columns([3, 1, 1])
        col_title.text_input(
            "Título",
            value=task.title,
            key=f"title_{task.id}",
            label_visibility="collapsed",
        )
        col_save.button(
            "Guardar",
            key=f"save_{task.id}",
            on_click=_update_task,
            args=(task.id,),
        )
        col_delete.button(
            "Eliminar",
            key=f"delete_{task.id}",
            on_click=_delete_task,
            args=(task.id,),
        )

        # Error pendiente del callback de guardado, mostrado una sola vez.
        error_key = f"update_error_{task.id}"
        if error_key in st.session_state:
            st.error(st.session_state.pop(error_key))


# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------

st.set_page_config(page_title="ToDo App", page_icon="✅")
st.title("📝 Lista de Tareas")

todo_list = _get_todo_list()

# Alta de tarea: el submit se procesa en _add_task (callback), que corre
# antes de este re-render y por tanto antes de dibujar la lista.
with st.form("todo_add_form"):
    st.text_input(
        "Nueva tarea",
        placeholder="Escribe el título de la tarea y pulsa Agregar…",
        key="todo_new_title",
    )
    st.form_submit_button("Agregar", type="primary", on_click=_add_task)

# Error pendiente del callback de alta, mostrado una sola vez.
if "add_error" in st.session_state:
    st.error(st.session_state.pop("add_error"))

st.divider()

# Filtro de visibilidad.
filter_label = st.radio(
    "Filtrar por estado",
    options=list(FILTER_OPTIONS.keys()),
    key="task_filter",
    horizontal=True,
)
task_filter = FILTER_OPTIONS[filter_label]

st.caption(
    f"Total: {todo_list.total_count} · "
    f"Pendientes: {todo_list.pending_count} · "
    f"Completadas: {todo_list.completed_count}"
)

# Listado: se itera sobre una SNAPSHOT (list_tasks devuelve una lista nueva)
# y las mutaciones solo ocurren en callbacks, antes de este render.
visible_tasks = todo_list.list_tasks(task_filter)

if not visible_tasks:
    st.info("No hay tareas para este filtro.")
else:
    for task in visible_tasks:
        _render_task(task)