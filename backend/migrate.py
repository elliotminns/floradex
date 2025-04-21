"""
Migration script to:
1. Rename 'plants' collection to 'userplants'
2. Create new 'plantspecies' collection
3. Fix references
"""
import sys
import os
from bson.objectid import ObjectId

# Import the database connection from your app's config
# Adjust this path as needed to match your project structure
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your existing database connection and client directly
from app.config import db, client  # Import both db and client from config

print("Connected to database successfully")

# 1. Rename plants collection to userplants
if 'plants' in db.list_collection_names():
    db.plants.rename('userplants')
    print("Successfully renamed 'plants' collection to 'userplants'")
else:
    print("'plants' collection does not exist")

# 2. Create plantspecies collection with sample data
if 'plantspecies' not in db.list_collection_names():
    # Sample plant species data
    sample_species = [
        {
            "name": "Monstera Deliciosa",
            "care_instructions": "Allow soil to dry between waterings",
            "watering_frequency": "Weekly",
            "sunlight_requirements": "Indirect bright light",
            "humidity": "Medium to high",
            "temperature": "65-85°F (18-29°C)",
            "fertilization": "Monthly during growing season"
        },
        {
            "name": "Snake Plant (Sansevieria)",
            "care_instructions": "Drought tolerant, let soil dry completely between waterings",
            "watering_frequency": "Every 2-3 weeks",
            "sunlight_requirements": "Low to bright indirect light",
            "humidity": "Low to average",
            "temperature": "60-85°F (15-29°C)",
            "fertilization": "Twice a year"
        }
    ]
    
    result = db.plantspecies.insert_many(sample_species)
    print(f"Created 'plantspecies' collection with {len(result.inserted_ids)} sample entries")
else:
    print("'plantspecies' collection already exists")

# 3. Update references in userplants and users if needed
# Add a default species_id to userplants that don't have one
userplants_without_species = list(db.userplants.find({"species_id": {"$exists": False}}))
if userplants_without_species:
    print(f"Found {len(userplants_without_species)} plants without species reference")
    
    # Get a default species ID to use
    default_species = db.plantspecies.find_one({})
    if default_species:
        default_species_id = str(default_species["_id"])
        
        # Update userplants to have a default species
        db.userplants.update_many(
            {"species_id": {"$exists": False}},
            {"$set": {"species_id": default_species_id}}
        )
        print(f"Updated plants with default species ID: {default_species_id}")
    else:
        print("No default species found")
else:
    print("All userplants have a species reference")

print("Migration completed!")