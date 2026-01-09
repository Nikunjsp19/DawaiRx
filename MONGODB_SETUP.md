# MongoDB Setup Guide

## Current Configuration

The project is configured to use **MongoDB Atlas** (cloud MongoDB) by default:

**Connection String:**
```
mongodb+srv://user:user@temp.tzhzodo.mongodb.net/DawaiRx
```

## Testing the Connection

After installing dependencies, test the connection:

```bash
make mongo-test
# OR
python -m src.persistence.mongo_test
```

## Configuration Options

### Option 1: Use Default Cloud Connection (Current)

No setup needed! The project is already configured to use MongoDB Atlas.

### Option 2: Use Environment Variable

You can override the connection string:

```bash
export MONGO_URI="mongodb+srv://user:password@your-cluster.mongodb.net/DawaiRx"
```

### Option 3: Use Local MongoDB

If you prefer to use local MongoDB with Docker:

```bash
# Start local MongoDB
make docker-up

# Set environment variable to use local
export MONGO_URI="mongodb://localhost:27017/dawai_rx"
```

Or set individual settings:

```bash
export MONGO_HOST="localhost"
export MONGO_PORT="27017"
export MONGO_DB="dawai_rx"
```

### Option 4: Use .env File

Create a `.env` file in the project root:

```bash
# .env
MONGO_URI=mongodb+srv://user:user@temp.tzhzodo.mongodb.net/DawaiRx?retryWrites=true&w=majority
```

Note: You'll need to install `python-dotenv` and load it in the config if you want to use .env files.

## MongoDB Atlas Setup (If Needed)

If you need to set up a new MongoDB Atlas cluster:

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Create a database user
4. Whitelist your IP address (or use 0.0.0.0/0 for development)
5. Get your connection string
6. Update `MONGO_URI` in `src/persistence/config.py` or set it as environment variable

## Troubleshooting

### Connection Timeout
- Check your internet connection
- Verify MongoDB Atlas cluster is running
- Ensure your IP is whitelisted in MongoDB Atlas

### Authentication Failed
- Verify username and password are correct
- Check database user permissions in MongoDB Atlas

### Local MongoDB Issues
- Ensure Docker is running: `docker ps`
- Check container status: `docker-compose ps`
- View logs: `docker-compose logs mongodb`

## Security Notes

⚠️ **Important**: The connection string contains credentials. 

- Never commit `.env` files to git (already in `.gitignore`)
- For production, use environment variables or secure secret management
- Consider using more secure credentials than "user:user"

