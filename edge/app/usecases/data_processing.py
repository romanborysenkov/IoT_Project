from app.entities.agent_data import AgentData
from app.entities.processed_agent_data import ProcessedAgentData

def process_agent_data(agent_data: AgentData) -> ProcessedAgentData:
    z_acceleration = agent_data.accelerometer.z
     
    if abs(z_acceleration) < 0.05:
        road_state = "good" 
    elif abs(z_acceleration) < 0.15:
        road_state = "average" 
    else:
        road_state = "poor" 

    processed_data = ProcessedAgentData(road_state=road_state, agent_data=agent_data)
    return processed_data
