#!/usr/bin/env python
"""Test AttrDict functionality"""
from database import AttrDict

d = AttrDict({'username': 'test', 'email': 'test@example.com'})
print(f'Dot access: {d.username}')
print(f'Bracket access: {d["email"]}')
print('SUCCESS - AttrDict works!')
