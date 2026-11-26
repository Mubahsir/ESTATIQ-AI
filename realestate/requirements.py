PROPERTY_TYPES = ["Residential Plot", "Commercial Plot", "House", "Villa", "Apartment", "Flat", "Studio Apartment", "Penthouse", "Hostel", "Shared Room", "Private Room", "Farmhouse", "Agricultural Land", "Commercial Building", "Office", "Shop", "Warehouse", "Industrial Property", "Mixed-Use Property", "Other"]
TRANSACTIONS = ["Buy", "Sell", "Rent", "Lease", "Investment", "Market Valuation Only"]

COMMON_SIZE = [("Size", "number"), ("Original measurement unit", "text")]
PLOT = COMMON_SIZE + [("Frontage", "number"), ("Depth", "number"), ("Corner plot", "bool"), ("Road width", "text"), ("Development / possession status", "text"), ("Utilities available", "text")]
HOUSE = COMMON_SIZE + [("Plot area", "number"), ("Bedrooms", "number"), ("Bathrooms", "number"), ("Floors", "number"), ("Parking spaces", "number"), ("Construction quality / condition", "text"), ("Furnished status", "text"), ("Year built", "number")]
APARTMENT = COMMON_SIZE + [("Bedrooms", "number"), ("Bathrooms", "number"), ("Floor number", "number"), ("Building floors", "number"), ("Building age", "number"), ("Lift / parking / amenities", "text"), ("Furnishing", "text")]
ROOM = [("Room count", "number"), ("Occupancy capacity", "number"), ("Attached bathroom", "bool"), ("Facilities", "text"), ("Utilities included", "bool")]
COMMERCIAL = COMMON_SIZE + [("Property usage", "text"), ("Floor", "text"), ("Frontage", "number"), ("Parking", "text"), ("Occupancy status", "text")]

def fields_for(property_type):
    if "Plot" in property_type or property_type == "Agricultural Land": return PLOT
    if property_type in ("House", "Villa", "Farmhouse"): return HOUSE
    if property_type in ("Apartment", "Flat", "Studio Apartment", "Penthouse"): return APARTMENT
    if property_type in ("Hostel", "Shared Room", "Private Room"): return ROOM
    if property_type in ("Office", "Shop", "Warehouse", "Commercial Building", "Industrial Property", "Mixed-Use Property"): return COMMERCIAL
    return COMMON_SIZE + [("Notes", "text")]
