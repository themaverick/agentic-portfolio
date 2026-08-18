db = db.getSiblingDB('portfolio_db');

// Collection: chat_sessions
db.chat_sessions.createIndex({ "session_id": 1 }, { unique: true });
db.chat_sessions.createIndex({ "ip_hash": 1, "created_at": -1 });
db.chat_sessions.createIndex(
    { "created_at": 1 },
    { expireAfterSeconds: 604800, partialFilterExpression: { auth_tier: "anonymous" } }
);

// Collection: jd_analyses
db.jd_analyses.createIndex({ "analysis_id": 1 }, { unique: true });
db.jd_analyses.createIndex({ "session_id": 1 });
db.jd_analyses.createIndex({ "created_at": -1 });

// Collection: agent_telemetry
db.agent_telemetry.createIndex({ "timestamp": -1 });
db.agent_telemetry.createIndex({ "session_id": 1, "timestamp": -1 });
db.agent_telemetry.createIndex({ "tool_calls_executed": 1 });