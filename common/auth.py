# # common/auth.py
# from functools import wraps
# from flask import request, jsonify, g
# from common.mongo_connection import MongoConnection
# from common.session_manage import SessionManager
# from config import (
#     MONGODB_CONNECTION_STRING,
#     MONGODB_DATABASE_NAME,
#     MONGODB_SESSION_COLLECTION
# )

# # # session manager instance 
# # _session_mgr = SessionManager(mongo=MongoConnection(connection_string=MONGODB_CONNECTION_STRING, db_name=MONGODB_DATABASE_NAME))

# # def get_current_user_from_token():
# #     token = request.cookies.get("token")
# #     if not token:
# #         return None
# #     data = _session_mgr.verify_token(token)
# #     return data

# def require_role(*allowed_roles):
#     """
#     Decorator: require user to be logged in and have one of allowed_roles.
#     Usage:
#       @require_role("admin","superadmin")
#     """
#     def decorator(f):
#         @wraps(f)
#         def wrapped(*args, **kwargs):
#             user = get_current_user_from_token()
#             if not user:
#                 return jsonify({"success": False, "message": "Unauthorized (no token)"}), 401
#             role = (user.get("role") or "").lower()
#             allowed_lower = [r.lower() for r in allowed_roles]
#             if allowed_roles and role not in allowed_lower:
#                 return jsonify({"success": False, "message": "Forbidden (insufficient role)"}), 403
#             # place user info into flask.g so route can inspect
#             try:
#                 from flask import g as _g
#                 _g.current_user = user
#             except Exception:
#                 pass
#             return f(*args, **kwargs)
#         return wrapped
#     return decorator
