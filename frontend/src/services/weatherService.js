import axios from 'axios';

const baseUrl = process.env.VUE_APP_BASE_URL;
const apiWeatherBaseUrl = `${baseUrl}/api/get-weather`;
const apisealocBaseUrl = `${baseUrl}/api/get-seaweather`;

// Land Weather
export async function fetchWeatherByCoordinates(lat, lon) {
  try {
    const response = await axios.post(
      apiWeatherBaseUrl,
      new URLSearchParams({ lat: lat, lon: lon }).toString(),
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
    console.error("Error fetching weather data:", error);
    return { error: error.message };
  }
}

// Sea Weather
export async function fetchSeaPostidByCoordinates(lat, lon) {
  try {
    const response = await axios.post(
      apisealocBaseUrl,
      new URLSearchParams({ lat: lat, lon: lon }).toString(), 
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
      console.error("Error fetching sea weather data:", error);
    return { error: error.message };
  }
}