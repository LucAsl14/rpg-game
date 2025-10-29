from __future__ import annotations
from src.core import *

class Chargable(Protocol):
    def charge(self, progress: float) -> None:
        """Charge the object with a progress value between 0 and 1."""
        pass

T = TypeVar("T")

class FutureReturnValue(Generic[T]):
    def __init__(self) -> None:
        self.value = None

    def set_value(self, value: Optional[T]) -> None:
        self.value = value

Action = Literal[
    "wait",
    "create",
    "charge",
    "get",
    "call",
    "call_until_true",
    "kill",
]
ValidAttrs = Literal[
    "initial_mouse_pos",
    "final_mouse_pos",
]

class Spell(Sprite):
    """Base class for spells. Performs a series of actions in a sequence.

    Define a sequence of actions by calling `add_action` with the action name
    as the first argument, followed by any positional and keyword arguments.

    Existing actions include:
    - "wait": Wait for a specified duration.
    - "create": Create an instance of a sprite class, the scene will be passed
      as the first argument, followed by any positional and keyword arguments.
    - "charge": Charge one or more objects, the objects must implement the
      `Chargable` protocol. This action will continuously call the `charge`
      method on the objects until the charge time is reached.
    - "get": Get an attribute from an object. Takes in an object and an
      attribute name as a string.
    - "call": Call a method on an object. Takes in an object, a method name as
      a string, and any positional or keyword arguments to pass to the method.
    - "call_until_true": Call a method on an object until it returns True.
      Takes in an object, a method name as a string, and any positional or
      keyword arguments to pass to the method.
    - "kill": Kill one or more sprites.
    """
    def __init__(self, scene: MainScene) -> None:
        super().__init__(scene, "DEFAULT")
        self.game = scene.game
        self.scene = scene
        self.current_timer = None
        self.actions = []
        self.actions_iter = None
        self.current_action = None
        # Debugging variable to count actions executed
        self.action_index = 0
        self.charge_time = 0.0
        self._initial_mouse_pos = None
        self._final_mouse_pos = None

    def update(self, dt: float) -> None:
        if self.actions_iter is None:
            self.actions_iter = iter(self.actions)
            self.current_action = next(self.actions_iter)
            self.action_index += 1

        assert self.current_action is not None

        try:
            future, action, args, kwargs = self.current_action
            success, return_val = getattr(self, "_" + action)(*args, **kwargs)
            if success and Debug.on("spell_messages"):
                Log.debug(f"Executed action #{self.action_index}: {action} "
                          f"with args: {args}, kwargs: {kwargs}")
                future.set_value(return_val)
                self.current_action = next(self.actions_iter)
                self.action_index += 1
        except StopIteration: # Reached end of actions
            self.kill()

    def draw(self, target: pygame.Surface) -> None:
        pass

    def set_charge_time(self, duration: float) -> None:
        """Set the time it takes to charge the spell."""
        self.charge_time = duration

    def add_action(self, action: Action, *args: Any, **kwargs: Any) -> FutureReturnValue:
        future = FutureReturnValue()
        self.actions.append([future, action, args, kwargs])
        return future

    def __getitem__(self, attr: ValidAttrs) -> FutureReturnValue:
        """Alias/shortcut for `self.add_action("get", self, attr)`."""
        return self.add_action("get", self, attr)

    def get(self, obj: Any, attr: str) -> FutureReturnValue:
        """Alias/shortcut for `self.add_action("get", obj, attr)`."""
        return self.add_action("get", obj, attr)

    def _wait_for_timer(self, duration: float) -> bool:
        if self.current_timer is None:
            self.current_timer = Timer(duration)
        if self.current_timer.done:
            self.current_timer = None
            return True
        return False

    def _wait(self, duration: float) -> tuple[bool, None]:
        return (self._wait_for_timer(duration), None)

    def _create(self, cls: Any, *args: Any, **kwargs: Any) -> tuple[bool, Any]:
        instance = cls(self.scene,
            *map(self._convert_if_future, args),
            **{k: self._convert_if_future(v) for k, v in kwargs.items()}
        )
        self.scene.add(instance)
        return (True, instance)

    def _charge(self, *objs: Chargable | FutureReturnValue[Chargable]) -> tuple[bool, None]:
        if self._initial_mouse_pos is None:
            self._initial_mouse_pos = self.scene.world_mouse_pos
        self._final_mouse_pos = self.scene.world_mouse_pos

        for obj in objs:
            self._call(obj, "charge", self.charge_progress)

        return (self._wait_for_timer(self.charge_time), None)

    @property
    def charge_progress(self) -> float:
        if self.current_timer is None:
            return 0.0
        return self.current_timer.progress

    @property
    def initial_mouse_pos(self) -> Vec:
        if self._initial_mouse_pos is None:
            return Vec(0, 0)
        return self._initial_mouse_pos

    @property
    def final_mouse_pos(self) -> Vec:
        if self._final_mouse_pos is None:
            return Vec(0, 0)
        return self._final_mouse_pos

    def _get(self, obj: Any, attr: str) -> tuple[bool, Any]:
        if isinstance(obj, FutureReturnValue):
            if obj.value is None:
                raise ValueError(f"Unable to get attribute '{attr}' at "
                         "action #{self.action_index} as the "
                         "value of the FutureReturnValue is unset.")
            return (True, getattr(obj.value, attr))

        return (True, getattr(obj, attr))

    def _call(self, obj: Any, func: str, *args: Any, **kwargs: Any) -> tuple[bool, Any]:
        if isinstance(obj, FutureReturnValue):
            if obj.value is None:
                raise ValueError(f"Unable to call function '{func}' at "
                         "action #{self.action_index} as the "
                         "value of the FutureReturnValue is unset.")
            return (True, getattr(obj.value, func)(
                *map(self._convert_if_future, args),
                **{k: self._convert_if_future(v) for k, v in kwargs.items()}
            ))

        return (True, getattr(obj, func)(
            *map(self._convert_if_future, args),
            **{k: self._convert_if_future(v) for k, v in kwargs.items()}
        ))

    def _call_until_true(self, obj: Any, func: str, *args: Any, **kwargs: Any) -> tuple[bool, Any]:
        """Call a function on an object until it returns True."""
        _, return_val = self._call(obj, func, *args, **kwargs)
        return (bool(return_val), return_val)

    def _kill(self, *objs: Sprite) -> tuple[bool, None]:
        for obj in objs:
            self._call(obj, "kill")
        return (True, None)

    def _convert_if_future(self, value: Any) -> Any:
        """If the value given is a FutureReturnValue, return its value.
        Otherwise, return the value as is.

        Raises:
            ValueError: If the FutureReturnValue has not been set.
        """
        if isinstance(value, FutureReturnValue):
            if value.value is None:
                raise ValueError("FutureReturnValue is unset.")
            return value.value
        return value
