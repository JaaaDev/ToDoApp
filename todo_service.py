"""Lógica pura de la ToDo App.

Este módulo contiene únicamente la lógica de dominio (tareas y su lista).
No importa Streamlit ni ninguna otra dependencia externa: solo la
biblioteca estándar (dataclasses, typing, uuid).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
from uuid import uuid4

_TASK_FILTERS = ("all", "pending", "completed")


def _validate_title(raw_title: str) -> str:
    """Valida y normaliza el título de una tarea.

    Devuelve el título sin espacios al inicio ni al final ("  x  " -> "x").
    Lanza ValueError si el título no es texto, está vacío o solo contiene
    espacios. Nunca devuelve un título vacío.
    """
    if not isinstance(raw_title, str):
        raise ValueError("El título debe ser una cadena de texto.")
    title = raw_title.strip()
    if not title:
        raise ValueError("El título no puede estar vacío ni contener solo espacios.")
    return title


@dataclass
class Task:
    """Una tarea individual de la lista."""

    id: str
    title: str
    done: bool = False

    def __post_init__(self) -> None:
        # Garantiza el invariante: el título siempre se almacena sin espacios
        # extra y nunca vacío, sin importar cómo se construya la instancia.
        self.title = _validate_title(self.title)


class TodoList:
    """Colección de tareas que preserva el orden de inserción.

    Internamente usa un diccionario id -> Task (ordenado por inserción en
    Python >= 3.7), lo que da acceso O(1) por id y operaciones de borrado
    que lanzan KeyError de forma natural cuando el id no existe.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def add(self, title: str) -> Task:
        """Agrega una tarea nueva y la devuelve.

        Lanza ValueError si el título es inválido (vacío o solo espacios).
        En ese caso la tarea NO se crea.
        """
        task = Task(id=uuid4().hex, title=_validate_title(title))
        self._tasks[task.id] = task
        return task

    def update(self, task_id: str, new_title: str) -> Task:
        """Renombra una tarea existente y la devuelve.

        Lanza KeyError si el id no existe y ValueError si el nuevo título
        es inválido. En caso de título inválido la tarea NO se modifica.
        """
        task = self._tasks[task_id]
        task.title = _validate_title(new_title)
        return task

    def delete(self, task_id: str) -> None:
        """Elimina una tarea por id.

        Lanza KeyError si el id no existe (nunca es idempotente).
        """
        del self._tasks[task_id]

    def toggle(self, task_id: str) -> Task:
        """Alterna una tarea entre completada y pendiente y la devuelve.

        Lanza KeyError si el id no existe.
        """
        task = self._tasks[task_id]
        task.done = not task.done
        return task

    def list_tasks(self, task_filter: str = "all") -> List[Task]:
        """Devuelve las tareas según el filtro, preservando el orden de
        inserción: "all" (todas), "pending" (pendientes) o "completed"
        (completadas). Lanza ValueError con cualquier otro valor.
        """
        if task_filter not in _TASK_FILTERS:
            raise ValueError(
                f"Filtro inválido: {task_filter!r}. "
                "Debe ser 'all', 'pending' o 'completed'."
            )
        if task_filter == "pending":
            return [task for task in self._tasks.values() if not task.done]
        if task_filter == "completed":
            return [task for task in self._tasks.values() if task.done]
        return list(self._tasks.values())

    @property
    def total_count(self) -> int:
        """Número total de tareas."""
        return len(self._tasks)

    @property
    def pending_count(self) -> int:
        """Número de tareas pendientes."""
        return sum(1 for task in self._tasks.values() if not task.done)

    @property
    def completed_count(self) -> int:
        """Número de tareas completadas."""
        return sum(1 for task in self._tasks.values() if task.done)