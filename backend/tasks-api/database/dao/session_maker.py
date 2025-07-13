from functools import wraps
from typing import Optional
from sqlalchemy import text
from ..models import async_session


def connection(isolation_level: Optional[str] = None, commit: bool = True):
    def decorator(method):
        @wraps(method)
        async def wrapper(*args, **kwargs):
            async with async_session() as session:
                try:
                    if isolation_level:
                        await session.execute(text(f'SET TRANSACTION ISOLATION LEVEL {isolation_level}'))
                    result = await method(*args, session=session, **kwargs)
                    if commit:
                        await session.commit()
                    return result
                except Exception as e:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        return wrapper
    return decorator
