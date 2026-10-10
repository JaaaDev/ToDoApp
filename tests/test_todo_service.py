"""Suite de tests de la ToDo App (todo_service).

Cubre los criterios de aceptación del PRD (AC-1..AC-8) más casos extra
(ids únicos, orden de inserción, contadores, KeyError en update).

Los tests importan únicamente el módulo bajo prueba y la biblioteca
estándar: NO dependen de Streamlit (ver AC-8).
"""

import pytest

from todo_service import TodoList


@pytest.fixture
def todo_list():
    """Una TodoList nueva por test: aislamiento total entre tests."""
    return TodoList()


# ---------------------------------------------------------------------------
# AC-1: add con título válido
# ---------------------------------------------------------------------------

def test_add_creates_task_pending_and_visible(todo_list):
    """AC-1: add con título válido crea la tarea con done=False y en la lista."""
    task = todo_list.add("comprar leche")

    assert task.title == "comprar leche"
    assert task.done is False
    assert todo_list.total_count == 1
    assert todo_list.list_tasks() == [task]


# ---------------------------------------------------------------------------
# AC-2: add con título vacío o solo espacios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "invalid_title",
    ["", "   ", "\t", "\n", " \t "],
    ids=["empty", "spaces", "tab", "newline", "mixed-blank"],
)
def test_add_rejects_blank_titles_without_creating(todo_list, invalid_title):
    """AC-2: título vacío o solo espacios lanza ValueError y no crea tareas."""
    todo_list.add("tarea previa")
    total_before = todo_list.total_count

    with pytest.raises(ValueError):
        todo_list.add(invalid_title)

    assert todo_list.total_count == total_before
    assert [task.title for task in todo_list.list_tasks()] == ["tarea previa"]


@pytest.mark.parametrize(
    "not_a_string", [None, 123, ["título"], {"título": 1}],
    ids=["none", "int", "list", "dict"],
)
def test_add_rejects_non_string_titles(todo_list, not_a_string):
    """AC-2 extra: títulos no textuales también lanzan ValueError."""
    with pytest.raises(ValueError):
        todo_list.add(not_a_string)
    assert todo_list.total_count == 0


# ---------------------------------------------------------------------------
# AC-3: trim de espacios al agregar
# ---------------------------------------------------------------------------

def test_add_trims_leading_and_trailing_whitespace(todo_list):
    """AC-3: '  comprar leche  ' se almacena como 'comprar leche'."""
    task = todo_list.add("  comprar leche  ")

    assert task.title == "comprar leche"
    stored = todo_list.list_tasks()[0]
    assert stored.title == "comprar leche"


# ---------------------------------------------------------------------------
# AC-4: update con título válido e inválido
# ---------------------------------------------------------------------------

def test_update_with_valid_title_changes_task(todo_list):
    """AC-4: update con título válido actualiza la tarea existente."""
    task = todo_list.add("título antiguo")

    updated = todo_list.update(task.id, "título nuevo")

    assert updated.id == task.id
    assert updated.title == "título nuevo"
    assert todo_list.list_tasks()[0].title == "título nuevo"


@pytest.mark.parametrize(
    "invalid_title", ["", "   "], ids=["empty", "spaces"],
)
def test_update_with_invalid_title_keeps_original(todo_list, invalid_title):
    """AC-4: update inválido lanza ValueError y el título original se mantiene."""
    task = todo_list.add("título original")

    with pytest.raises(ValueError):
        todo_list.update(task.id, invalid_title)

    assert task.title == "título original"
    assert todo_list.list_tasks()[0].title == "título original"


# ---------------------------------------------------------------------------
# AC-5: delete
# ---------------------------------------------------------------------------

def test_delete_removes_task_from_list(todo_list):
    """AC-5: delete hace desaparecer la tarea de la lista."""
    task = todo_list.add("tarea a eliminar")

    todo_list.delete(task.id)

    assert todo_list.total_count == 0
    assert task not in todo_list.list_tasks()


def test_delete_missing_id_raises_key_error(todo_list):
    """AC-5: delete de un id inexistente lanza KeyError."""
    todo_list.add("tarea")

    with pytest.raises(KeyError):
        todo_list.delete("id-que-no-existe")


def test_delete_same_task_twice_raises_key_error(todo_list):
    """AC-5 extra: delete no es idempotente; repetirlo lanza KeyError."""
    task = todo_list.add("tarea")
    todo_list.delete(task.id)

    with pytest.raises(KeyError):
        todo_list.delete(task.id)


# ---------------------------------------------------------------------------
# AC-6: toggle
# ---------------------------------------------------------------------------

def test_toggle_cycles_pending_to_completed_to_pending(todo_list):
    """AC-6: toggle alterna pendiente→completada y completada→pendiente."""
    task = todo_list.add("tarea")
    assert task.done is False

    toggled = todo_list.toggle(task.id)
    assert toggled.done is True
    assert toggled.id == task.id

    toggled_back = todo_list.toggle(task.id)
    assert toggled_back.done is False


def test_toggle_missing_id_raises_key_error(todo_list):
    """AC-6 extra: toggle de un id inexistente lanza KeyError."""
    with pytest.raises(KeyError):
        todo_list.toggle("id-que-no-existe")


# ---------------------------------------------------------------------------
# AC-7: filtros
# ---------------------------------------------------------------------------

@pytest.fixture
def mixed_list(todo_list):
    """Lista con una tarea pendiente y una completada."""
    pending = todo_list.add("tarea pendiente")
    completed = todo_list.add("tarea completada")
    todo_list.toggle(completed.id)
    return todo_list


def test_filter_all_returns_every_task(mixed_list):
    """AC-7: filtro 'all' devuelve todas las tareas (y es el valor por defecto)."""
    assert len(mixed_list.list_tasks("all")) == 2
    assert len(mixed_list.list_tasks()) == 2


def test_filter_pending_returns_only_not_done(mixed_list):
    """AC-7: filtro 'pending' devuelve solo las tareas no completadas."""
    result = mixed_list.list_tasks("pending")

    assert len(result) == 1
    assert result[0].title == "tarea pendiente"
    assert all(not task.done for task in result)


def test_filter_completed_returns_only_done(mixed_list):
    """AC-7: filtro 'completed' devuelve solo las tareas completadas."""
    result = mixed_list.list_tasks("completed")

    assert len(result) == 1
    assert result[0].title == "tarea completada"
    assert all(task.done for task in result)


@pytest.mark.parametrize(
    "invalid_filter",
    ["", "ALL", "Done", "pending ", "unknown", None, 42],
    ids=["empty", "uppercase", "wrong-case", "trailing-space", "unknown", "none", "int"],
)
def test_invalid_filter_raises_value_error(todo_list, invalid_filter):
    """AC-7: filtro fuera de all/pending/completed lanza ValueError."""
    todo_list.add("tarea")

    with pytest.raises(ValueError):
        todo_list.list_tasks(invalid_filter)


# ---------------------------------------------------------------------------
# AC-8: desacoplamiento de Streamlit
# ---------------------------------------------------------------------------

def test_todo_service_has_no_streamlit_dependency():
    """AC-8: el módulo no importa Streamlit (desacoplamiento total)."""
    import ast
    import pathlib
    import sys

    import todo_service

    # 1) Análisis estático: ningún "import" del módulo referencia streamlit.
    module_path = pathlib.Path(todo_service.__file__)
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert not any(
        name.lower().startswith("streamlit") for name in imported_modules
    ), f"El módulo importa streamlit: {sorted(imported_modules)}"

    # 2) Verificación en runtime: importar todo_service no carga streamlit.
    assert "streamlit" not in sys.modules


# ---------------------------------------------------------------------------
# Extras: ids únicos, orden de inserción, contadores, KeyError en update
# ---------------------------------------------------------------------------

def test_task_ids_are_unique(todo_list):
    """Extra: cada tarea recibe un id distinto."""
    tasks = [todo_list.add(f"tarea {i}") for i in range(100)]

    ids = [task.id for task in tasks]
    assert len(ids) == len(set(ids))


def test_list_preserves_insertion_order(todo_list):
    """Extra: list_tasks preserva el orden de inserción."""
    titles = ["primera", "segunda", "tercera", "cuarta"]
    for title in titles:
        todo_list.add(title)

    assert [task.title for task in todo_list.list_tasks()] == titles


def test_counters_are_consistent_with_states(todo_list):
    """Extra: total = pending + completed según el estado real de las tareas."""
    first = todo_list.add("primera")
    todo_list.add("segunda")
    third = todo_list.add("tercera")
    todo_list.toggle(first.id)
    todo_list.toggle(third.id)

    assert todo_list.total_count == 3
    assert todo_list.pending_count == 1
    assert todo_list.completed_count == 2
    assert todo_list.total_count == todo_list.pending_count + todo_list.completed_count


def test_update_missing_id_raises_key_error(todo_list):
    """Extra: update de un id inexistente lanza KeyError."""
    with pytest.raises(KeyError):
        todo_list.update("id-que-no-existe", "nuevo título")