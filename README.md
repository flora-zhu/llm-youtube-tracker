**Problem Statement**

LLM YouTube Tracker automatically follows several popular YouTube channels whose focus revolves around LLMs. It maintains a table hosted on a public page that includes information about the channel name, video date, video link, topics covered in the video, and a summary of the video. It is updated automatically as new videos are added.


**Methodology**

Videos are retrieved using YouTube Data API v3. Transcripts of the video captions are fetched using youtube-transcript-api. Groq/Llama is utilized for identification of relevant videos, AI summarization, and topics for each video. GitHub Actions is used for scheduling an update once every 6 hours. The website is hosted on Netlify, and updates automatically. An LLM topic filter is implemented using Groq in order to ensure that irrelevant videos from the channels are not included in the table.

**Evaluation Dataset**

The channels I picked were Yannic Kilcher, Matt Wolfe, Fireship, and Wes Roth, for multiple reasons. First, all four of them consistently upload quality video content that is relevant to the topic of LLMs. Second, they all generally have captions and transcriptions available that are able to be retrieved using YouTube's API, allowing me to use Groq to analyze their topics. 

**Evaluation Methods**

Videos were manually verified to ensure that summaries matched the actual content and that videos that the filter skipped were non-topical. 

**Experimental Results**

The site is hosted here: https://llm-youtube-tracker.netlify.app/

YouTube's API blocks cloud servers such as the one utilized in GitHub Actions, meaning using the automatic update feature results in a failure to retrieve the transcript required for the topics and summary columns. Because of this, I ran the script locally to generate the table and disabled the GitHub Action responsible for automatic updates. However, if not for the cloud-blocking issue, there would be full functionality with automatic updates.

Here is a screenshot of the table, as appears on the webpage:

<img width="2880" height="1800" alt="image" src="https://github.com/user-attachments/assets/9d2d9891-d0f1-4144-bfbb-fd8421cc1f79" />
