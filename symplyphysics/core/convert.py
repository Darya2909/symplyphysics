from sympy import Expr, Add, Mul, sympify
from sympy.vector import VectorAdd, VectorMul, Vector as SymVector
from sympy.physics.units import Quantity as SymQuantity

from ..core.vectors.vectors import Vector, vector_from_sympy_vector
from ..core.coordinate_systems.coordinate_systems import CoordinateSystem
from ..core.quantity_decorator import assert_equivalent_dimension
from ..core.symbols.quantities import Quantity


def convert_to(value: Quantity, target_unit: SymQuantity) -> Expr:
    """
    Convert ``value`` to its scale factor with ``value`` unit represented as ``target_unit``.
    """
    target_quantity = Quantity(target_unit)
    assert_equivalent_dimension(value, value.dimension.name, "convert_to",
        target_quantity.dimension)
    return sympify(value.scale_factor) * (1 / sympify(target_quantity.scale_factor))


def expr_to_vector(expr: Expr, coordinate_system: CoordinateSystem) -> Vector:
    if isinstance(expr, Mul):
        expr = VectorMul(*expr.args)
    if isinstance(expr, Add):
        expr = VectorAdd(*expr.args)
    if not isinstance(expr, SymVector):
        raise TypeError(f"Expression cannot be converted to SymPy Vector: {str(expr)}")
    vector = vector_from_sympy_vector(expr, coordinate_system)
    components = [Quantity(c) for c in vector.components]
    return Vector(components, coordinate_system)
