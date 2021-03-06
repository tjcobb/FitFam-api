# app.py
import pymongo
import os
from lib import ResponseBuilder
from flask import Flask, request

app = Flask(__name__)


# MongoClient = pymongo.MongoClient("mongodb+srv://fitbio-app:RIAUhKkDs4mVwHFH@tylercobbtestcluster-atvya.mongodb.net/test?retryWrites=true")
MongoClient = pymongo.MongoClient(os.environ["MONGO_URI"])
FitbioDB = MongoClient[os.environ["FITBIO_DB"]]
WeightCollection = FitbioDB[os.environ["WEIGHT_COLLECTION"]]


@app.route("/weight", methods=["GET"])
def get_weight():
    user_id = request.environ["event"]["requestContext"]["identity"]["cognitoIdentityId"]
    res = WeightCollection.find_one({"user_id": user_id}) or {}

    # ObjectId not serializable, there is probably a better way to do this
    if "_id" in res:
        res["_id"] = str(res["_id"])

    return ResponseBuilder.success(res)


@app.route("/weight", methods=["POST"])
def insert_weight():
    # TODO - Sort by date?
    # TODO - Consider max doc size of 16MB if we are storing all weights for someone in single doc
    user_id = request.environ["event"]["requestContext"]["identity"]["cognitoIdentityId"]
    existing = WeightCollection.find_one({"user_id": user_id}) or {}
    existing_weights = existing["weights"] if "weights" in existing else []
    new_weight_dates = [w["date"] for w in request.json["weights"]]
    merged_weights = request.json["weights"]

    for old_weight in [w for w in existing_weights if w["date"] not in new_weight_dates]:
        merged_weights.append(old_weight)

    WeightCollection.update_one(
        {"user_id": user_id},
        {"$set": {"weights": merged_weights}},
        upsert=True
    )

    return ResponseBuilder.success({"message": "Done"})
