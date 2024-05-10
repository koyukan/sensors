using UnityEngine;
using NativeWebSocket;
using System;

public class WebSocketManager : MonoBehaviour
{
    public static WebSocketManager Instance { get; private set; }
    private WebSocket websocket;
    public event Action<string> OnMessageReceived;

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    async void Start()
    {
        websocket = new WebSocket("ws://127.0.0.1:5678");

        websocket.OnMessage += (bytes) =>
        {
            string message = System.Text.Encoding.UTF8.GetString(bytes);
            Debug.Log("Received from WebSocket: " + message);
            OnMessageReceived?.Invoke(message);
        };

        await websocket.Connect();
    }

    void Update()
    {
        if (websocket != null)
        {
            websocket.DispatchMessageQueue();
        }
    }

    async void OnDestroy()
    {
        if (websocket != null)
        {
            await websocket.Close();
        }
    }

    public void RegisterOnMessageReceived(Action<string> callback)
    {
        OnMessageReceived += callback;
    }
}

