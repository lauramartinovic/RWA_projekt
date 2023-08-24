from decouple import AutoConfig
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from backend.model import UserInDB
from security import authenticate_user, create_access_token, hash_password

# Inicijalizacija konfiguracije
config = AutoConfig(search_path="./")

app = FastAPI()

# Funkcije pomoćnice za rad s ObjectId
def str_to_objectid(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
def objectid_to_str(id: ObjectId) -> str:
    return str(id)

# Startup i Shutdown eventi za bazu podataka
@app.on_event("startup")
async def startup():
    MONGO_URI = config('MONGO_URI', default="mongodb://localhost:27017")
    app.mongodb_client = AsyncIOMotorClient(MONGO_URI)
    app.mongodb = app.mongodb_client.MovieApp

    app.films_collection = app.mongodb.Films
    app.users_collection = app.mongodb.Users
    app.reviews_collection = app.mongodb.Reviews
    app.recommendations_collection = app.mongodb.Recommendations

@app.on_event("shutdown")
async def shutdown():
    app.mongodb_client.close()

# Endpointovi za filmove
@app.get("/movies/")
async def list_movies():
    movies = []
    async for movie in app.films_collection.find():
        movie["_id"] = objectid_to_str(movie["_id"])
        movies.append(movie)
    return movies

@app.post("/movies/")
async def create_movie(movie: dict):
    result = await app.films_collection.insert_one(movie)
    return JSONResponse(content={"_id": str(result.inserted_id)})

@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: str):
    object_id = str_to_objectid(movie_id)
    result = await app.films_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {"status": "success"}

# Endpointovi za korisnike
@app.post("/users/register")
async def register_user(user: UserInDB):
    existing_user = await app.users_collection.find_one({'username': user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = hash_password(user.password)
    user_data = {
        "username": user.username,
        "hashed_password": hashed_password
    }
    
    await app.users_collection.insert_one(user_data)
    # Return username and not the password or hash for security
    return {"username": user.username}


@app.post("/users/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(request, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.put("/users/{user_id}")
async def update_user(user_id: str, user: dict):
    object_id = str_to_objectid(user_id)
    result = await app.users_collection.replace_one({"_id": object_id}, user)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success"}

# Endpointovi za recenzije
@app.post("/reviews/")
async def create_review(review: dict):
    existing_review = await app.reviews_collection.find_one({'user_id': review['user_id'], 'movie_id': review['movie_id']})
    if existing_review:
        raise HTTPException(status_code=400, detail="Review already exists for this user and movie")
    await app.reviews_collection.insert_one(review)
    return review

@app.put("/reviews/{review_id}")
async def update_review(review_id: str, review: dict):
    object_id = str_to_objectid(review_id)
    result = await app.reviews_collection.replace_one({"_id": object_id}, review)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"status": "success"}

@app.delete("/reviews/{review_id}")
async def delete_review(review_id: str):
    object_id = str_to_objectid(review_id)
    result = await app.reviews_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"status": "success"}

# Endpointovi za preporuke
@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str):
    object_id = str_to_objectid(user_id)
    user = await app.users_collection.find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "recommendations": []}
