// Delete all Job nodes and their relationships
MATCH (j:Job)
DETACH DELETE j
RETURN "All jobs deleted";
