import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport

# Default to local test DB if not set
TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://test_admin:test_secret@localhost:5433/test_inventory",
)

TABLES_TO_TRUNCATE = [
    "stock_lots",
    "items",
    "recipe_ingredients",
    "recipes",
    "ingredient_aliases",
    "ingredient_substitutions",
    "ingredient_references",
    "product_references",
]


@pytest.fixture(scope="session")
def test_engine():
    return create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)


@pytest.fixture(scope="session", autouse=True)
async def _patch_engine(test_engine):
    """Patch the app's DB engine and SessionLocal to use the test database."""
    import db.session as session_mod

    session_mod.engine = test_engine
    session_mod.SessionLocal = sessionmaker(
        autocommit=False,
        expire_on_commit=False,
        autoflush=False,
        bind=test_engine,
        class_=AsyncSession,
    )


@pytest.fixture(scope="session", autouse=True)
async def _create_tables(test_engine, _patch_engine):
    """Create all tables at session start (safety net if alembic hasn't run)."""
    from db.base import Base
    # Import all models so Base.metadata knows about them
    import models.item  # noqa: F401
    import models.product_reference  # noqa: F401
    import models.stock_lot  # noqa: F401
    import models.ingredient_reference  # noqa: F401
    import models.ingredient_alias  # noqa: F401
    import models.recipe  # noqa: F401
    import models.recipe_ingredient  # noqa: F401
    import models.ingredient_substitution  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
async def _truncate_tables(test_engine):
    """Truncate all tables before each test for clean state."""
    async with test_engine.begin() as conn:
        await conn.execute(
            text(f"TRUNCATE {', '.join(TABLES_TO_TRUNCATE)} CASCADE")
        )


@pytest.fixture
async def db_session(test_engine):
    """Provide a fresh async DB session for direct CRUD/service calls."""
    session = AsyncSession(test_engine, expire_on_commit=False)
    yield session
    try:
        await session.close()
    except Exception:
        pass


@pytest.fixture
async def client(test_engine):
    """Provide an httpx AsyncClient wired to the FastAPI app with test DB."""
    from main import app
    from db.session import get_db

    session = AsyncSession(test_engine, expire_on_commit=False)

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    try:
        await session.close()
    except Exception:
        pass


# ── Factory Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def make_product(db_session):
    """Factory to create ProductReference rows."""
    from crud.product_reference import create_product
    from models.product_reference import ProductType

    async def _make(
        name="Test Butter",
        barcode=None,
        product_type=ProductType.PLU,
        package_quantity=250.0,
        package_unit="g",
        **kwargs,
    ):
        return await create_product(
            db_session,
            name=name,
            barcode=barcode,
            product_type=product_type,
            package_quantity=package_quantity,
            package_unit=package_unit,
            **kwargs,
        )

    return _make


@pytest.fixture
def make_ingredient(db_session):
    """Factory to create IngredientReference rows."""
    from crud.ingredient_reference import create_ingredient_reference

    async def _make(name="butter", normalized_name=None):
        return await create_ingredient_reference(
            db_session, name=name, normalized_name=normalized_name or name
        )

    return _make


@pytest.fixture
def make_alias(db_session):
    """Factory to create IngredientAlias rows."""
    from crud.ingredient_alias import create_ingredient_alias

    async def _make(alias, ingredient_id):
        return await create_ingredient_alias(
            db_session, alias=alias, ingredient_id=ingredient_id
        )

    return _make


@pytest.fixture
def make_stock(db_session):
    """Factory to add stock (creates lot + refreshes item cache)."""
    from crud.item import add_stock
    from models.item import Locations

    async def _make(
        product_reference_id,
        location=Locations.FRIDGE,
        quantity=500.0,
        unit="g",
    ):
        return await add_stock(
            db_session,
            product_reference_id=product_reference_id,
            location=location,
            quantity=quantity,
            unit=unit,
        )

    return _make


@pytest.fixture
def make_recipe(db_session):
    """Factory to create Recipe with optional RecipeIngredients."""
    from crud.recipe import create_recipe
    from crud.recipe_ingredient import create_recipe_ingredient

    async def _make(title="Test Recipe", ingredients=None, instructions=None):
        recipe = await create_recipe(
            db_session,
            title=title,
            instructions=instructions or ["Step 1"],
        )
        if ingredients:
            for ing in ingredients:
                await create_recipe_ingredient(
                    db_session,
                    recipe_id=recipe.id,
                    ingredient_text=ing["text"],
                    canonical_ingredient_id=ing["ingredient_id"],
                    quantity=ing["quantity"],
                    unit=ing["unit"],
                )
        return recipe

    return _make


@pytest.fixture
def make_substitution(db_session):
    """Factory to create IngredientSubstitution rows."""
    from crud.ingredient_substitution import create_substitution

    async def _make(original_id, substitute_id, ratio=1.0, quality_score=7, notes=None):
        return await create_substitution(
            db_session,
            original_ingredient_id=original_id,
            substitute_ingredient_id=substitute_id,
            ratio=ratio,
            quality_score=quality_score,
            notes=notes,
        )

    return _make


@pytest.fixture
async def populated_inventory(
    make_product, make_ingredient, make_alias, make_stock, make_recipe, make_substitution
):
    """
    Composite fixture: realistic test scenario with products, ingredients,
    aliases, stock, substitutions, and a recipe.
    """
    from models.item import Locations

    # Ingredients
    butter = await make_ingredient(name="butter")
    flour = await make_ingredient(name="flour")
    sugar = await make_ingredient(name="sugar")
    margarine = await make_ingredient(name="margarine")
    olive_oil = await make_ingredient(name="olive oil")

    # Products
    p_butter = await make_product(name="Store Butter", package_quantity=227, package_unit="g")
    p_flour = await make_product(name="All Purpose Flour", package_quantity=2267, package_unit="g")
    p_sugar = await make_product(name="White Sugar", package_quantity=1814, package_unit="g")
    p_margarine = await make_product(name="Imperial Margarine", package_quantity=454, package_unit="g")
    p_olive_oil = await make_product(name="Extra Virgin Olive Oil", package_quantity=750, package_unit="ml")

    # Aliases
    await make_alias("Store Butter", butter.id)
    await make_alias("All Purpose Flour", flour.id)
    await make_alias("White Sugar", sugar.id)
    await make_alias("Imperial Margarine", margarine.id)
    await make_alias("Extra Virgin Olive Oil", olive_oil.id)

    # Stock
    await make_stock(p_butter.id, Locations.FRIDGE, 227.0, "g")
    await make_stock(p_flour.id, Locations.CUPBOARD, 2267.0, "g")
    await make_stock(p_sugar.id, Locations.CUPBOARD, 1814.0, "g")
    await make_stock(p_margarine.id, Locations.FRIDGE, 454.0, "g")
    await make_stock(p_olive_oil.id, Locations.CUPBOARD, 750.0, "ml")

    # Substitutions
    await make_substitution(butter.id, margarine.id, ratio=1.0, quality_score=8)
    await make_substitution(margarine.id, butter.id, ratio=1.0, quality_score=8)

    # Recipe: needs butter + flour + sugar
    recipe = await make_recipe(
        title="Simple Cookies",
        ingredients=[
            {"text": "butter", "ingredient_id": butter.id, "quantity": 113.0, "unit": "g"},
            {"text": "flour", "ingredient_id": flour.id, "quantity": 240.0, "unit": "g"},
            {"text": "sugar", "ingredient_id": sugar.id, "quantity": 200.0, "unit": "g"},
        ],
    )

    return {
        "ingredients": {
            "butter": butter,
            "flour": flour,
            "sugar": sugar,
            "margarine": margarine,
            "olive_oil": olive_oil,
        },
        "products": {
            "butter": p_butter,
            "flour": p_flour,
            "sugar": p_sugar,
            "margarine": p_margarine,
            "olive_oil": p_olive_oil,
        },
        "recipe": recipe,
    }
