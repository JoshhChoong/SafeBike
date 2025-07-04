def calculate_edge_weight(edge, current_time, vehicle_type):
    # Base weight (distance + historical collision risk)
    base_weight = edge.length * edge.collision_risk
    
    # Rush hour multiplier
    rush_multiplier = get_rush_hour_multiplier(edge, current_time)
    
    # Vehicle-specific adjustments
    vehicle_multiplier = get_vehicle_multiplier(edge, vehicle_type)
    
    # Final weight
    final_weight = base_weight * rush_multiplier * vehicle_multiplier
    
    return final_weight

# there may be different weights for weather, car model and make, road conditions 
# pot holes, police cars 



## will code this myself l8

def get_rush_hour_multiplier(edge, current_time):
    # get the hour 
    # get the day 
    return 

def get_vehicle_multiplier():
    return 

# I need a function that takes:
# edge (the road segment)
# time (when are we traveling)
# And returns: how much worse this road is right now

def calculate_badness(road, time):
    # Start with base badness = 1 (normal)
    badness = 1.0
    
    # IF it's rush hour AND this road is bad during rush hour:
    if is_rush_hour(time) and is_bad_road(road):
        badness = make_it_worse(badness)
    
    return badness



def analyze_daily_accidents():
    daily_counts = []
    for day in range(7):
        count = int(input(f"Day {day+1} accidents: "))
        daily_counts.append(count)
    
    print(f"Total week: {sum(daily_counts)}")
    print(f"Average: {sum(daily_counts)/7:.1f}")
    print(f"Worst day: {max(daily_counts)}")


analyze_daily_accidents()