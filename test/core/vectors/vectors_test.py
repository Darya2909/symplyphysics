from collections import namedtuple
from pytest import fixture, raises
from sympy import atan, pi, sqrt, symbols, sin, cos
from sympy.vector import Vector as SympyVector, express
from symplyphysics import (Quantity, dimensionless, units, QuantityVector, Vector, errors)
from symplyphysics.core.coordinate_systems.coordinate_systems import CoordinateSystem, coordinates_rotate, coordinates_transform

Args = namedtuple("Args", ["C"])


@fixture(name="test_args")
def test_args_fixture() -> Args:
    C = CoordinateSystem()
    return Args(C=C)


# Test Vector constructor


def test_basic_vector(test_args: Args) -> None:
    vector = Vector([1, 2], test_args.C)
    assert vector.components == [1, 2]
    assert vector.coordinate_system == test_args.C


def test_empty_vector(test_args: Args) -> None:
    vector = Vector([], test_args.C)
    assert len(vector.components) == 0
    assert vector.coordinate_system == test_args.C


# Test Vector.from_sympy_vector()


def test_basic_sympy_to_array_conversion(test_args: Args) -> None:
    vector = Vector.from_sympy_vector(test_args.C.coord_system.i + 2 * test_args.C.coord_system.j,
        test_args.C)
    assert vector.components == [1, 2, 0]
    assert vector.coordinate_system == test_args.C


def test_order_sympy_to_array_conversion(test_args: Args) -> None:
    vector = Vector.from_sympy_vector(2 * test_args.C.coord_system.j + test_args.C.coord_system.i,
        test_args.C)
    assert vector.components == [1, 2, 0]


def test_skip_dimension_sympy_to_array_conversion(test_args: Args) -> None:
    vector = Vector.from_sympy_vector(test_args.C.coord_system.i + 2 * test_args.C.coord_system.k,
        test_args.C)
    assert vector.components == [1, 0, 2]


def test_empty_sympy_to_array_conversion(test_args: Args) -> None:
    vector = Vector.from_sympy_vector(SympyVector.zero, test_args.C)
    assert len(vector.components) == 0
    assert vector.coordinate_system == test_args.C


# Does not support non SymPy Vectors
def test_only_scalar_sympy_to_array_conversion(test_args: Args) -> None:
    with raises(AttributeError):
        Vector.from_sympy_vector(test_args.C.coord_system.x, test_args.C)
    x1 = symbols("x1")
    with raises(AttributeError):
        Vector.from_sympy_vector(x1, test_args.C)


def test_free_variable_sympy_to_array_conversion(test_args: Args) -> None:
    x1 = symbols("x1")
    vector = Vector.from_sympy_vector(test_args.C.coord_system.i * x1, test_args.C)
    assert vector.components == [x1, 0, 0]
    assert vector.coordinate_system == test_args.C


def test_non_cartesian_array_to_sympy_conversion() -> None:
    C1 = CoordinateSystem(CoordinateSystem.System.CYLINDRICAL)
    i, j, _ = C1.coord_system.base_vectors()
    vector = Vector.from_sympy_vector(i + 2 * j, C1)
    assert vector.components == [1, 2, 0]
    assert vector.coordinate_system == C1


def test_rotate_coordinates_array_to_sympy_conversion(test_args: Args) -> None:
    sympy_vector = test_args.C.coord_system.i + test_args.C.coord_system.j
    vector = Vector.from_sympy_vector(sympy_vector, test_args.C)
    assert vector.components == [1, 1, 0]
    theta = symbols("theta")
    B = coordinates_rotate(test_args.C, theta, test_args.C.coord_system.k)
    i, j, _ = B.coord_system.base_vectors()
    sympy_transformed_vector = express(sympy_vector, B.coord_system)
    assert sympy_transformed_vector == ((sin(theta) + cos(theta)) * i +
        (-sin(theta) + cos(theta)) * j)
    transformed_vector = Vector.from_sympy_vector(sympy_transformed_vector, B)
    assert transformed_vector.components == [sin(theta) + cos(theta), -sin(theta) + cos(theta), 0]
    assert transformed_vector.coordinate_system == B
    # Do the same via vector_rebase
    vector_rebased = vector.rebase(B)
    assert vector_rebased.components == [sin(theta) + cos(theta), -sin(theta) + cos(theta), 0]


def test_multiple_coord_systems_sympy_to_array_conversion(test_args: Args) -> None:
    C1 = CoordinateSystem(CoordinateSystem.System.CYLINDRICAL)
    r, _, _ = C1.coord_system.base_scalars()
    _, _, k = C1.coord_system.base_vectors()
    with raises(TypeError):
        Vector.from_sympy_vector(test_args.C.coord_system.i + 2 * k, test_args.C)
    with raises(TypeError):
        Vector.from_sympy_vector(test_args.C.coord_system.i + r * test_args.C.coord_system.k, C1)


def test_basic_array_to_sympy_conversion(test_args: Args) -> None:
    sympy_vector = Vector([1, 2], test_args.C).to_sympy_vector()
    assert sympy_vector == test_args.C.coord_system.i + 2 * test_args.C.coord_system.j


def test_skip_dimension_array_to_sympy_conversion(test_args: Args) -> None:
    sympy_vector = Vector([1, 0, 2], test_args.C).to_sympy_vector()
    assert sympy_vector == test_args.C.coord_system.i + 2 * test_args.C.coord_system.k


def test_4d_array_to_sympy_conversion(test_args: Args) -> None:
    sympy_vector = Vector([1, 0, 2, 5], test_args.C).to_sympy_vector()
    assert sympy_vector == test_args.C.coord_system.i + 2 * test_args.C.coord_system.k


def test_empty_array_to_sympy_conversion() -> None:
    sympy_vector = Vector([]).to_sympy_vector()
    assert sympy_vector == SympyVector.zero
    # only comparison with Vector.zero works
    assert sympy_vector != 0
    assert sympy_vector is not None


def test_rotate_coordinates_sympy_to_array_conversion(test_args: Args) -> None:
    theta = symbols("theta")
    B = coordinates_rotate(test_args.C, theta, test_args.C.coord_system.k)
    i, j, _ = B.coord_system.base_vectors()
    sympy_vector = Vector([1, 2], B).to_sympy_vector()
    assert sympy_vector == i + 2 * j
    transformed_vector = express(sympy_vector, test_args.C.coord_system)
    assert transformed_vector == ((-2 * sin(theta) + cos(theta)) * test_args.C.coord_system.i +
        (sin(theta) + 2 * cos(theta)) * test_args.C.coord_system.j)
    # Do the same via vector_rebase
    vector_rebased = Vector([1, 2], B).rebase(test_args.C)
    assert vector_rebased.components == [
        -2 * sin(theta) + cos(theta), sin(theta) + 2 * cos(theta), 0
    ]


# Test Vector.rebase()


def test_basic_vector_rebase(test_args: Args) -> None:
    vector = Vector([test_args.C.coord_system.x, test_args.C.coord_system.y], test_args.C)

    # B is located at [1, 2] origin instead of [0, 0] of test_args.C
    Bi = test_args.C.coord_system.locate_new(
        "B", test_args.C.coord_system.i + 2 * test_args.C.coord_system.j)
    B = CoordinateSystem(test_args.C.coord_system_type, Bi)
    x, y, _ = B.coord_system.base_scalars()
    vector_rebased = vector.rebase(B)
    assert vector_rebased.coordinate_system == B
    # Original field is not changed
    assert vector.coordinate_system == test_args.C
    assert vector_rebased.components == [x + 1, y + 2, 0]


# Simple numbers in vector are not scalars - they cannot be properly
# rebased to new coordinate system.
def test_plain_vector_rebase(test_args: Args) -> None:
    vector = Vector([1, 2], test_args.C)
    # B is located at [1, 2] origin instead of [0, 0] of test_args.C
    Bi = test_args.C.coord_system.locate_new(
        "B", test_args.C.coord_system.i + 2 * test_args.C.coord_system.j)
    B = CoordinateSystem(test_args.C.coord_system_type, Bi)
    vector_rebased = vector.rebase(B)
    assert vector_rebased.coordinate_system == B
    # Original field is not changed
    assert vector.coordinate_system == test_args.C
    assert vector_rebased.components == [1, 2, 0]


# Simple parameters in vector are not scalars - they cannot be properly
# rebased to new coordinate system.
def test_parameters_vector_rebase(test_args: Args) -> None:
    parameter = symbols("parameter")
    vector = Vector([parameter, parameter], test_args.C)

    # B is located at [1, 2] origin instead of [0, 0] of test_args.C
    Bi = test_args.C.coord_system.locate_new(
        "B", test_args.C.coord_system.i + 2 * test_args.C.coord_system.j)
    B = CoordinateSystem(test_args.C.coord_system_type, Bi)
    vector_rebased = vector.rebase(B)
    assert vector_rebased.coordinate_system == B
    # Original field is not changed
    assert vector.coordinate_system == test_args.C
    assert vector_rebased.components == [parameter, parameter, 0]


# Rotation does not require vector defined with base scalars.
def test_rotate_vector_rebase(test_args: Args) -> None:
    vector = Vector([1, 2], test_args.C)
    point = [1, 2]
    p1 = test_args.C.coord_system.origin.locate_new(
        "p1", point[0] * test_args.C.coord_system.i + point[1] * test_args.C.coord_system.j)
    p1_coordinates = p1.express_coordinates(test_args.C.coord_system)
    assert p1_coordinates[0] == point[0]
    assert p1_coordinates[1] == point[1]

    B = coordinates_rotate(test_args.C, pi / 4, test_args.C.coord_system.k)
    p1_coordinates_in_b = p1.express_coordinates(B.coord_system)
    assert p1_coordinates_in_b[0] != point[0]

    transformed_point = [p1_coordinates_in_b[0], p1_coordinates_in_b[1], 0]
    vector_rebased = vector.rebase(B)
    assert vector_rebased.coordinate_system == B
    assert vector_rebased.components == [3 * sqrt(2) / 2, sqrt(2) / 2, 0]
    assert vector_rebased.components == transformed_point


# Test non-cartesian coordinate systems


def test_spherical_vector_create(test_args: Args) -> None:
    vector = Vector([1, 2], test_args.C)
    B = coordinates_transform(test_args.C, CoordinateSystem.System.SPHERICAL)
    # vector should have r = sqrt(5) in polar coordinates
    # vector is in XY-plane, so phi angle should be pi/2
    # theta angle is atan(2/1)
    vector_rebased = vector.rebase(B)
    assert vector_rebased.coordinate_system == B
    assert vector_rebased.components == [sqrt(5), atan(2), pi / 2]


# Test QuantityVector constructor


def test_basic_quantity_vector(test_args: Args) -> None:
    q1 = Quantity(1)
    q2 = Quantity(2)
    vector = QuantityVector([q1, q2], test_args.C)
    assert [vector.components[0].scale_factor,
        vector.components[1].scale_factor] == [q1.scale_factor, q2.scale_factor]
    assert vector.coordinate_system == test_args.C
    assert vector.dimension == dimensionless


def test_empty_quantity_vector() -> None:
    vector = QuantityVector([])
    assert len(vector.components) == 0
    assert vector.dimension == dimensionless


def test_invalid_dimension_quantity_vector() -> None:
    q1 = Quantity(1)
    q2 = Quantity(2, dimension=units.length)
    with raises(errors.UnitsError):
        QuantityVector([q1, q2])


# Test QuantityVector.components()


def test_basic_to_quantities(test_args: Args) -> None:
    q1 = Quantity(1)
    q2 = Quantity(2)
    vector = QuantityVector([q1, q2], test_args.C)
    assert [vector.components[0].scale_factor,
        vector.components[1].scale_factor] == [q1.scale_factor, q2.scale_factor]
    assert [vector.components[0].dimension,
        vector.components[1].dimension] == [q1.dimension, q2.dimension]


# Test QuantityVector.from_sympy_vector()


def test_basic_quantities_from_sympy_vector(test_args: Args) -> None:
    vector = QuantityVector.from_sympy_vector(
        test_args.C.coord_system.i + 2 * test_args.C.coord_system.j, test_args.C)
    assert [vector.components[0].scale_factor, vector.components[1].scale_factor] == [1, 2]
    assert vector.dimension == dimensionless


def test_dimensions_manual_quantities_from_sympy_vector(test_args: Args) -> None:
    vector = QuantityVector.from_sympy_vector(test_args.C.coord_system.i +
        2 * test_args.C.coord_system.j,
        test_args.C,
        dimension=units.length)
    assert [vector.components[0].scale_factor, vector.components[1].scale_factor] == [1, 2]
    assert vector.dimension == units.length


def test_dimensions_auto_quantities_from_sympy_vector(test_args: Args) -> None:
    vector = QuantityVector.from_sympy_vector(
        test_args.C.coord_system.i * units.meter + 2 * test_args.C.coord_system.j * units.meter,
        test_args.C)
    assert [vector.components[0].scale_factor, vector.components[1].scale_factor] == [1, 2]
    assert vector.dimension == units.length


def test_invalid_dimension_quantities_from_sympy_vector(test_args: Args) -> None:
    with raises(errors.UnitsError):
        QuantityVector.from_sympy_vector(
            test_args.C.coord_system.i * units.meter +
            2 * test_args.C.coord_system.j * units.second, test_args.C)


# Test QuantityVector.rebase()


def test_basic_quantities_rebase(test_args: Args) -> None:
    q1 = Quantity(1)
    q2 = Quantity(2)
    vector = QuantityVector([q1 * test_args.C.coord_system.x, q2 * test_args.C.coord_system.y],
        test_args.C)
    # B is located at [1, 2] origin instead of [0, 0] of test_args.C
    Bi = test_args.C.coord_system.locate_new(
        "B", test_args.C.coord_system.i + 2 * test_args.C.coord_system.j)
    B = CoordinateSystem(test_args.C.coord_system_type, Bi)
    vector_rebased = vector.rebase(B)
    assert vector_rebased.coordinate_system == B
    # Original field is not changed
    assert vector.coordinate_system == test_args.C
    # Quantities are not scalar values - they cannot be properly rebased
    assert [vector_rebased.components[0].scale_factor, vector_rebased.components[1].scale_factor
           ] == [test_args.C.coord_system.x, 2 * test_args.C.coord_system.y]


def test_rotate_quantities_rebase(test_args: Args) -> None:
    q1 = Quantity(1)
    q2 = Quantity(2)
    vector = QuantityVector([q1, q2], test_args.C)
    point = [1, 2]
    p1 = test_args.C.coord_system.origin.locate_new(
        "p1", point[0] * test_args.C.coord_system.i + point[1] * test_args.C.coord_system.j)
    p1_coordinates = p1.express_coordinates(test_args.C.coord_system)
    assert p1_coordinates[0] == point[0]
    assert p1_coordinates[1] == point[1]

    B = coordinates_rotate(test_args.C, pi / 4, test_args.C.coord_system.k)
    p1_coordinates_in_b = p1.express_coordinates(B.coord_system)
    assert p1_coordinates_in_b[0] != point[0]

    vector_rebased = vector.rebase(B)
    assert vector_rebased.coordinate_system == B
    assert [vector_rebased.components[0].scale_factor,
        vector_rebased.components[1].scale_factor] == [3 * sqrt(2) / 2,
        sqrt(2) / 2]
    assert [p1_coordinates_in_b[0], p1_coordinates_in_b[1]] == [3 * sqrt(2) / 2, sqrt(2) / 2]


def test_spherical_quantities_rebase(test_args: Args) -> None:
    q1 = Quantity(1)
    q2 = Quantity(2)
    vector = QuantityVector([q1, q2], test_args.C)
    B = coordinates_transform(test_args.C, CoordinateSystem.System.SPHERICAL)
    # vector should have r = sqrt(5) in polar coordinates
    # vector is in XY-plane, so phi angle should be pi/2
    # theta angle is atan(2/1)
    vector_rebased = vector.rebase(B)
    assert vector_rebased.coordinate_system == B
    assert [
        vector_rebased.components[0].scale_factor, vector_rebased.components[1].scale_factor,
        vector_rebased.components[2].scale_factor
    ] == [sqrt(5), atan(2), pi / 2]
