from pydantic import BaseModel
from typing import List, Optional

class Movie(BaseModel):
    title: str
    year: int
    genres: List[str]
    director: str
    plot: str
    actors: List[str]

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str

class Review(BaseModel):
    user_id: str
    movie_id: str
    rating: float
    comment: Optional[str]

class Recommendation(BaseModel):
    user_id: str
    movie_id: str
