import axios from 'axios' 

const baseUrl = process.env.VUE_APP_BASE_URL;
const apiassistBaseUrl = `${baseUrl}/predict/chat`;
const apipredictBaseUrl = `${baseUrl}/predict`

// AI Predict Request
export async function requestPredict(formdata, token=null) {
    try {
      const response = await axios.post(
        apipredictBaseUrl,
        formdata,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            "Authorization": `Bearer ${token}`,
          },
          withCredentials: true,
        }
      );
  
      console.log(response)

      if (response.status === 200) {
        return { status : response.status, 
          data : response.data.data}
      } else {
        throw { response: { status: 204, data: { message: "No content" } } }
      }
    } catch (error) {
      if (error.response){
        console.error("Error Predict:", error.response.status);

      if ([422, 204, 405, 415, 400].includes(error.response.status)) { 
        console.log(`Error Status: ${error.response.status}`);
        return { status: error.response.status, 
              data: error.response.data };
      }

      return { status: error.response.status, message: "Unhandled error" };
    }
      if (error.request) {
        return error.request
      }
    }
  }

// ChatGPT Assistant Request
export async function fetchchatgptAssist(thread_id, run_id) {
  try {
    const response = await axios.post(
      apiassistBaseUrl,
      new URLSearchParams({ thread_id: thread_id, run_id: run_id }).toString(),
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        }
      }
    );

    if (response.status === 200) {
        return response.data.data;
    } else {
      return null
    }
  } catch (error) {
    console.error("Error Request chatGPT assistant data:", error);
    return { error: error.message };
  }
}