"""Test how Neo4j nodes work with dict conversion"""
import os
from app import create_app
from database import get_neo4j_db, safe_run, _node_to_dict, AttrDict

app = create_app('development')

with app.app_context():
    db = get_neo4j_db()
    
    with db.session() as session:
        # Get a user node
        query = "MATCH (u:User) RETURN u LIMIT 1"
        result = session.run(query)
        record = list(result)[0]
        
        print("=" * 60)
        print("Raw Neo4j Record:")
        print("=" * 60)
        print(f"type(record) = {type(record)}")
        print(f"record.keys() = {record.keys()}")
        print(f"record['u'] = {record['u']}")
        print(f"type(record['u']) = {type(record['u'])}")
        
        node = record['u']
        print()
        print("=" * 60)
        print("Neo4j Node Details:")
        print("=" * 60)
        print(f"hasattr(node, 'labels') = {hasattr(node, 'labels')}")
        print(f"hasattr(node, 'id') = {hasattr(node, 'id')}")
        print(f"hasattr(node, 'keys') = {hasattr(node, 'keys')}")
        print(f"node.labels = {node.labels}")
        print(f"node.id = {node.id}")
        print(f"node.keys() = {node.keys()}")
        print(f"dict(node) = {dict(node)}")
        
        print()
        print("=" * 60)
        print("Node properties:")
        print("=" * 60)
        for key in node.keys():
            print(f"  node['{key}'] = {node[key]}")
        
        print()
        print("=" * 60)
        print("AttrDict conversion:")
        print("=" * 60)
        attr_dict = AttrDict(node)
        print(f"attr_dict = {attr_dict}")
        print(f"type(attr_dict) = {type(attr_dict)}")
        print(f"'username' in attr_dict = {'username' in attr_dict}")
        if 'username' in attr_dict:
            print(f"attr_dict['username'] = {attr_dict['username']}")
            print(f"attr_dict.username = {attr_dict.username}")
        else:
            print("WARNING: 'username' not in attr_dict!")
            print(f"attr_dict.keys() = {list(attr_dict.keys())}")
        
        print()
        print("=" * 60)
        print("_node_to_dict conversion:")
        print("=" * 60)
        converted = _node_to_dict(node)
        print(f"converted = {converted}")
        print(f"type(converted) = {type(converted)}")
        print(f"'username' in converted = {'username' in converted}")
        if 'username' in converted:
            print(f"converted['username'] = {converted['username']}")
            print(f"converted.username = {converted.username}")
        else:
            print("WARNING: 'username' not in converted!")
            print(f"converted.keys() = {list(converted.keys())}")

