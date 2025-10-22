from pydantic import BaseModel, model_validator
from datetime import date, time, datetime
from typing import List

# Define the schema for an available slot, to be inserted into MongoDB

class AvailabilityCreate(BaseModel):
    scraping_datetime: datetime
    region: str
    city: str
    club: str
    court: str
    availability_date: date
    availability_time: time
    availability_duration: int
    
class AvailabilityRead(BaseModel):
    region: List[str] | None = None
    city: List[str] | None = None
    club: List[str] | None = None
    court: List[str] | None = None
    availability_date: date
    availability_time: time | None = None
    availability_duration: int | None = None
    
class AvailabilityDelete(BaseModel):
    region: List[str] | None = None
    city: List[str] | None = None
    club: List[str] | None = None
    court: List[str] | None = None
    availability_date: date

    @model_validator(mode = 'before')
    @classmethod
    def at_least_one_not_none(cls, values):
        pass
        # if not any(values.)


    

