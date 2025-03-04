import axios from "@/axios"; // Axios 인스턴스 임포트

const baseUrl = process.env.VUE_APP_BASE_URL;
const apimulddaeBaseUrl = `${baseUrl}/api/tide-cycles`;

export async function fetchMulddae(date) {
  console.log(`Call_fetchMulddae : ${date}`);
  try {
    const response = await axios.get(apimulddaeBaseUrl,{
        params: {
          nowdate: date,
        },
      }
    );

    if (response.status === 200) {
      return response.data.data;

    } else {
      return null;
    }
  } catch (error) {
    console.error("Error fetching mulddae data:", error);
    return null;
  }
}