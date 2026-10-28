local logins = {}
for _, key in ipairs(redis.call('keys', 'session:*')) do
    table.insert(logins, redis.call('hget', key, 'user_login'))
end
return logins
