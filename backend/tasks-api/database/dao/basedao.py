from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import selectinload
from ..models import async_session, Base
from typing import List, Any, Dict, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=Base)


class BaseDAO(Generic[T]):
    model: type[T]

    @classmethod
    async def find_one_or_none_by_id(self, session: AsyncSession, data_id: int):
        try:
            return await session.get(self.model, data_id)
        except SQLAlchemyError as e:
            print(f'Error: {e}')
            raise
    
    @classmethod
    async def find_one_or_none(self, session: AsyncSession, filters: BaseModel, offset: int = 0,
                               order_by_lmbd=None):
        filter_dict = filters.model_dump(exclude_unset=True, exclude_none=True)
        try:
            query = select(self.model).filter_by(**filter_dict).offset(offset).limit(1)
            if order_by_lmbd:
                query = query.order_by(order_by_lmbd(self.model))
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise
    
    # Expiremental
    @classmethod
    async def find_one_or_none_by_expression(self, session: AsyncSession, filters: BaseModel, expr):
        filter_dict = filters.model_dump(exclude_unset=True)
        try:
            query = select(self.model).filter_by(**filter_dict).where(expr(self.model))
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise
    
    @classmethod
    async def find_all(self, session: AsyncSession, filters: BaseModel | None, filter_lmbd=None,
                        order_by_lmbd=None, limit: int | None = None, offset: int = 0,
                        fetch_relationships=False):
        if filters:
            filter_dict = filters.model_dump(exclude_unset=True, exclude_none=True)
        else:
            filter_dict = {}
        try:
            query = select(self.model).filter_by(**filter_dict).limit(limit).offset(offset)
            if filter_lmbd:
                query = query.where(filter_lmbd(self.model))
            if order_by_lmbd:
                query = query.order_by(order_by_lmbd(self.model))
            if fetch_relationships:
                query = query.options(*[selectinload(self.model.__dict__[key]) for key in inspect(self.model).relationships.keys()])
            result = await session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise
    
    @classmethod
    async def add(self, session: AsyncSession, values: BaseModel):
            values_dict = values.model_dump(exclude_unset=True)
            new_instance = self.model(**values_dict)
            session.add(new_instance)
            try:
                await session.flush()
            except SQLAlchemyError as e:
                await session.rollback()
                raise e
            return new_instance

    @classmethod
    async def add_many(self, session: AsyncSession, instances: List[BaseModel]):
            values_list = [item.model_dump(exclude_unset=True) for item in instances]
            new_instances = [self.model(**values) for values in values_list]
            session.add_all(new_instances)
            try:
                await session.flush()
            except SQLAlchemyError as e:
                await session.rollback()
                raise e
            return new_instances
    
    @classmethod
    async def update_one_by_id(self, session: AsyncSession, data_id: int, values: BaseModel):
        values_dict = values.model_dump(exclude_unset=True, exclude_none=True)
        try:
            record = await session.get(self.model, data_id)
            for key, value in values_dict.items():
                setattr(record, key, value)
            await session.flush()
        except SQLAlchemyError as e:
            print(e)
            raise(e)
    
    @classmethod
    async def update_many(self, session: AsyncSession, filters: BaseModel | None, values: BaseModel,
                          filter_lmbd = None):
        if filters:
            filter_dict = filters.model_dump(exclude_unset=True, exclude_none=True)
        else:
            filter_dict = {}
        values_dict = values.model_dump(exclude_unset=True)
        try:
            if filter_lmbd:
                query = (
                    sqlalchemy_update(self.model)
                    .filter_by(**filter_dict)
                    .where(filter_lmbd(self.model))
                    .values(**values_dict)
                )
            else:
                query = (
                    sqlalchemy_update(self.model)
                    .filter_by(**filter_dict)
                    .values(**values_dict)
                )
            result = await session.execute(query)
            await session.flush()
            return result.rowcount
        except SQLAlchemyError as e:
            print(f'Error in mass update: {e}')
            raise e
    
    @classmethod
    async def rank(self, session: AsyncSession, id, filters: BaseModel | None, order_by_lmbd):
        if filters:
            filter_dict = filters.model_dump(exclude_unset=True, exclude_none=True)
        else:
            filter_dict = {}
        try:
            rank_query = select(self.model.id, func.rank().over(order_by=order_by_lmbd(self.model)).label('rank')).filter_by(**filter_dict)
            subq = rank_query.subquery()
            stmt = select(subq.c.rank).where(subq.c.id == id)
            # if filter_dict:
            #     for key, value in filter_dict.items():
            #         stmt = stmt.where(getattr(self.model, key) == value)
            result = await session.execute(stmt)
            return result.scalar()
            # query = select(func.dense_rank().over(order_by=order_by_lmbd(self.model)), primary_key) #.filter_by(**filter_dict))
            # result = await session.execute(query)
            # return result.scalars().all()
        except SQLAlchemyError as e:
            print(f'Error in dense rank: {e}')
            raise e
