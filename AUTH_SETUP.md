# Authentication Setup Guide

## Quick Setup Steps

### 1. Install Authentication Dependencies

```bash
pip install bcrypt pyjwt python-jose[cryptography]
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Set JWT Secret Key

You need to set a secure secret key for JWT token signing. Choose one of these methods:

#### Option A: Environment Variable (Recommended)
```bash
export JWT_SECRET_KEY="your-secret-key-here"
```

#### Option B: Create .env File
Create a `.env` file in the project root:
```
JWT_SECRET_KEY=your-secret-key-here
```

#### Generate a Secure Key
Run this command to generate a secure random key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and use it as your `JWT_SECRET_KEY`.

**⚠️ Important:** 
- Use a strong, random secret key in production
- Never commit the secret key to version control
- The default key in code is for development only

### 3. Start the Server

```bash
python -m src.cli.main web
```

Or with custom host/port:
```bash
python -m src.cli.main web --host 127.0.0.1 --port 8000
```

### 4. Access the Application

1. Open your browser and go to: `http://127.0.0.1:8000/login`
2. You'll see the login page

### 5. Create Your First Account

On the login page:
- Enter a **User ID** (e.g., "admin", "user1", or your email)
- Enter a **Password** (minimum 6 characters)
- Click **"Register"** link at the bottom (or click "Sign In" if you already have an account)

The system will:
- Create your account in MongoDB
- Hash your password securely
- Log you in automatically
- Redirect you to the main dashboard

### 6. Use the Application

Once logged in:
- Your authentication token is stored in browser localStorage
- All API requests automatically include your token
- You can only see and access your own data
- Click "Sign Out" in the header to logout

## Troubleshooting

### "ModuleNotFoundError: No module named 'bcrypt'"
**Solution:** Install dependencies:
```bash
pip install bcrypt pyjwt python-jose[cryptography]
```

### "Could not validate credentials" or 401 errors
**Solution:** 
- Make sure `JWT_SECRET_KEY` is set
- Try logging in again (token might have expired)
- Clear browser localStorage and login again

### "User already exists" when registering
**Solution:** 
- Use a different User ID
- Or login with existing credentials

### MongoDB Connection Issues
**Solution:**
- Check your MongoDB connection string in environment variables
- Ensure MongoDB is accessible
- Check network/firewall settings

## How It Works

1. **Registration/Login:** Creates account or verifies credentials
2. **Token Generation:** Server issues a JWT token (valid for 7 days)
3. **Token Storage:** Browser stores token in localStorage
4. **Automatic Auth:** All API calls include the token in headers
5. **Data Isolation:** All data is scoped to your user_id

## Security Notes

- Passwords are hashed with bcrypt (never stored in plain text)
- JWT tokens are signed and cannot be forged
- Tokens expire after 7 days (user must login again)
- All data queries are filtered by user_id
- HTTPS should be used in production

## Example Usage

```bash
# 1. Install dependencies
pip install bcrypt pyjwt python-jose[cryptography]

# 2. Set secret key
export JWT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"

# 3. Start server
python -m src.cli.main web

# 4. Open browser
# Go to: http://127.0.0.1:8000/login
# Register/Login and start using the app!
```

