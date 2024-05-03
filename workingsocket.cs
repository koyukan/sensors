using System.Collections;
using UnityEngine;
using NativeWebSocket;

public class SensorDataReceiver : MonoBehaviour
{
    WebSocket websocket;

    async void Start()
    {
        websocket = new WebSocket("ws://127.0.0.1:5678");

        websocket.OnOpen += () =>
        {
            Debug.Log("Connection open!");
        };

        websocket.OnMessage += (bytes) =>
{
    var message = System.Text.Encoding.UTF8.GetString(bytes);
    Debug.Log("Received OnMessage! Data: " + message);
    try
    {
        var data = JsonUtility.FromJson<RotationData>(message);

        // Apply rotation to the object
        
        
        
        transform.eulerAngles = new Vector3(data.pitch, data.yaw, data.roll);
    }
    catch (System.Exception ex)
    {
        Debug.LogError("Error processing message: " + ex.Message);
    }
};


        websocket.OnError += (e) =>
        {
            Debug.LogError("Error from WebSocket: " + e);
        };

        try
        {
            await websocket.Connect();
        }
        catch (System.Exception ex)
        {
            Debug.LogError("Failed to connect: " + ex.Message);
        }
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

    [System.Serializable]
    public class RotationData
    {
        public float roll;
        public float pitch;
        public float yaw;
    }
}
