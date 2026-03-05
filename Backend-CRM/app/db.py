from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from app.models import Base
    from sqlalchemy import inspect, text
    
    try:
        async with engine.begin() as conn:
            # Check if tables already exist by querying directly
            try:
                result = await conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users')"))
                users_exists = result.scalar()
                
                if users_exists:
                    print("✅ Database tables already exist, skipping creation")
                    return
            except Exception as check_error:
                # If check fails, try to create anyway
                print(f"⚠️  Could not check if tables exist: {check_error}")
            
            # Otherwise, create tables
            print("🔄 Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully")
    except Exception as e:
        error_msg = str(e).lower()
        # If tables already exist or schema issues, that's fine - database was restored
        if any(keyword in error_msg for keyword in [
            "already exists", "duplicate", "does not exist", 
            "no schema", "schema", "relation"
        ]):
            print(f"⚠️  Database initialization skipped (tables may already exist): {type(e).__name__}")
            # Don't raise - let the app continue
        else:
            print(f"❌ Error initializing database: {e}")
            # Still don't raise - app might work if tables exist
            pass

