using UnityEngine;

public class ObjectRotation : MonoBehaviour
{
    void Start()
    {
        if (WebSocketManager.Instance != null)
        {
            WebSocketManager.Instance.RegisterOnMessageReceived(OnMessageReceived);
        }
    }

    void OnMessageReceived(string message)
    {
        Debug.Log("Received Message: " + message);  // Log the raw message for debugging

        // Parse the JSON message to extract quaternion data
        QuaternionData data = JsonUtility.FromJson<QuaternionData>(message);

        // Check if the quaternion array has the expected length
        if (data.quaternion == null || data.quaternion.Length != 4)
        {
            Debug.LogError("Quaternion data is null or not in the correct format.");
            return;
        }

		
	
        Quaternion newRotation = (new Quaternion(-data.quaternion[1], -data.quaternion[3], -data.quaternion[2], data.quaternion[0]));
        Debug.Log($"Applying Quaternion Rotation: {newRotation}");  // Log the quaternion values

        transform.rotation = newRotation;  // Apply the quaternion rotation directly
    }

    [System.Serializable]
    public class QuaternionData
    {
        public float[] quaternion;  // Assuming the order [w, x, y, z]
    }
}

