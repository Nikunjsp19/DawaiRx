# JWT Secret Key - How It Works

## What is JWT?

**JWT (JSON Web Token)** is a compact, URL-safe token format used for authentication. Think of it like a **signed ID card** that proves who you are.

## Structure of a JWT Token

A JWT token has 3 parts, separated by dots (`.`):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZXhwIjoxNzAwMDAwMDAwfQ.signature
│─────────────────────││──────────────────────────────││──────────│
        Header              Payload (data)              Signature
```

### 1. Header
Contains metadata about the token:
```json
{
  "alg": "HS256",  // Algorithm used (HMAC SHA-256)
  "typ": "JWT"     // Type of token
}
```

### 2. Payload
Contains the actual data (claims):
```json
{
  "sub": "user123",           // Subject (user_id)
  "exp": 1700000000,          // Expiration timestamp
  "iat": 1699000000           // Issued at timestamp
}
```

### 3. Signature
A cryptographic signature that proves the token is authentic.

## How the Secret Key Works

### Purpose of the Secret Key

The **secret key** is like a **master password** that:
1. **Signs** the token when it's created (proves it came from your server)
2. **Verifies** the token when it's received (proves it hasn't been tampered with)

### The Signing Process

```
1. Server creates token payload:
   {
     "sub": "user123",
     "exp": 1700000000,
     "iat": 1699000000
   }

2. Server signs it with secret key:
   signature = HMAC-SHA256(
     base64(header) + "." + base64(payload),
     SECRET_KEY
   )

3. Final token = header.payload.signature
```

### The Verification Process

```
1. Client sends token to server

2. Server extracts header and payload

3. Server recalculates signature using SECRET_KEY:
   expected_signature = HMAC-SHA256(
     base64(header) + "." + base64(payload),
     SECRET_KEY
   )

4. Server compares:
   - If signatures match → Token is VALID ✅
   - If signatures don't match → Token is INVALID ❌
```

## Why Is the Secret Key Important?

### 1. **Prevents Token Forgery**
Without the secret key, an attacker cannot create valid tokens:
```python
# Attacker tries to create fake token
fake_token = create_token_without_secret({"sub": "admin"})

# Server verifies with secret key
verify_token(fake_token, SECRET_KEY)  # ❌ FAILS - Invalid signature!
```

### 2. **Prevents Token Tampering**
If someone modifies the payload, the signature won't match:
```python
# Original token
token = "header.payload.signature"

# Attacker modifies payload
tampered = "header.MODIFIED_PAYLOAD.signature"

# Server verifies
verify_token(tampered, SECRET_KEY)  # ❌ FAILS - Signature mismatch!
```

### 3. **Stateless Authentication**
The server doesn't need to store tokens in a database. It can verify tokens just by checking the signature:
```python
# No database lookup needed!
user_id = verify_token(token, SECRET_KEY)  # Returns user_id from token
```

## Security Considerations

### ✅ Good Practices

1. **Use a Strong, Random Secret**
   ```bash
   # Generate secure random key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Keep Secret Key Private**
   - Never commit to version control
   - Use environment variables
   - Don't share with unauthorized people

3. **Use HTTPS in Production**
   - Prevents token interception
   - Protects secret key transmission

4. **Set Token Expiration**
   - Limits damage if token is stolen
   - Forces periodic re-authentication

### ❌ Common Mistakes

1. **Weak Secret Key**
   ```python
   # BAD - Too simple
   SECRET_KEY = "password123"
   
   # GOOD - Random and long
   SECRET_KEY = "xkH_e2Bam0YrWNCoj_Hqc_jMV-tVOi-6ddFws3Zf-yw"
   ```

2. **Exposing Secret Key**
   ```python
   # BAD - In code
   SECRET_KEY = "my-secret"
   
   # GOOD - In environment
   SECRET_KEY = os.getenv("JWT_SECRET_KEY")
   ```

3. **Using Same Secret Everywhere**
   - Use different secrets for different environments
   - Dev, staging, production should have different keys

## How It Works in DawaiRx

### 1. Login Flow
```
User logs in → Server verifies password → Server creates JWT with secret
```

### 2. Token Creation
```python
# In src/auth/utils.py
def create_access_token(data: Dict[str, Any]) -> str:
    payload = {
        "sub": data["sub"],  # user_id
        "exp": datetime.utcnow() + timedelta(hours=7*24),  # 7 days
        "iat": datetime.utcnow()
    }
    
    # Sign with secret key
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token
```

### 3. Token Verification
```python
# In src/auth/middleware.py
def get_current_user_id(credentials):
    token = credentials.credentials
    
    # Verify with secret key
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    
    # Extract user_id
    user_id = payload.get("sub")
    return user_id
```

### 4. Protected Routes
```python
@app.post("/api/run")
async def run_comparison(user_id: str = Depends(get_current_user_id)):
    # user_id is automatically extracted from token
    # Token was verified using SECRET_KEY
    # If token is invalid, request is rejected
```

## Real-World Analogy

Think of JWT like a **driver's license**:

- **Payload** = Your personal info (name, DOB, address)
- **Signature** = Official seal/stamp from DMV
- **Secret Key** = The DMV's official stamping machine

**Without the secret key:**
- Anyone could create fake licenses
- You couldn't verify if a license is real

**With the secret key:**
- Only the DMV (your server) can create valid licenses
- Anyone can verify a license is real by checking the seal
- If someone tries to modify the license, the seal won't match

## Summary

**JWT Secret Key Purpose:**
1. ✅ **Signs tokens** - Proves they came from your server
2. ✅ **Verifies tokens** - Proves they haven't been tampered with
3. ✅ **Prevents forgery** - Attackers can't create valid tokens
4. ✅ **Enables stateless auth** - No database lookup needed

**Key Points:**
- Secret key must be kept **private and secure**
- Use a **strong, random** secret key
- Same secret is used for **signing AND verifying**
- Without the secret, tokens are **useless** (security!)

