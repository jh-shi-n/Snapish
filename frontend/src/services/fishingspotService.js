import axios from "axios";

const baseUrl = process.env.VUE_APP_BASE_URL; 
const apiDBBaseUrl = `${baseUrl}/api/spots`;


export async function fetchFishingSpotAll() {
    try {
      const response = await axios.get(
        apiDBBaseUrl,
      );
      if (response.status === 200) {
        return response.data.data;
  
      } else {
        return null
      }
    } catch (error) {
      console.error("Error fetching DB:", error);
      return { error: error.message };
    }
  }


  export async function fetchFishingSpotDetail(spotId) {
    try {
      const response = await axios.get(
        `${apiDBBaseUrl}/${spotId}`
      );
      if (response.status === 200) {
        return response.data.data;
  
      } else {
        return null
      }
    } catch (error) {
      console.error("Error fetching DB:", error);
      return { error: error.message };
    }
  }