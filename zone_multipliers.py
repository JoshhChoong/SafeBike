# danger zones for rush hour driver use case 

GTA_RUSH_ZONES = {
    "highway_interchanges": {
        "multiplier": 4.5,  
        "zones": [
            "401_DVP", "401_427", "Gardiner_DVP", 
            "QEW_427", "404_401", "400_401"
        ]
    },
    "downtown_core": {
        "multiplier": 3.2,
        "zones": [
            "King_St_corridor", "Queen_St_downtown",
            "Bay_St_financial", "University_Ave"
        ]
    },
    "major_arterials": {
        "multiplier": 2.8,
        "zones": [
            "Bloor_St", "Eglinton_Ave", "Finch_Ave",
            "Steeles_Ave", "Lawrence_Ave"
        ]
    },
    "streetcar_routes": {
        "multiplier": 2.5,
        "zones": [
            "Spadina_Ave", "Bathurst_St", "Ossington_Ave"
        ]
    }
}

RUSH_HOUR_TIMES = {
    "morning": (7, 9),    
    "evening": (16, 19),  
    "friday_evening": (15, 20)  
}