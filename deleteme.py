import asyncio
import websockets

async def websocket_client(uri):
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to server")
            while True:
                message = await websocket.recv()
                print("Received from server:", message)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    uri = "ws://127.0.0.1:5678"  # Ensure this is correct
    asyncio.run(websocket_client(uri))
