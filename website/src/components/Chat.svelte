<script>
  import { createEventDispatcher } from "svelte";
  import { PUBLIC_OPENAI_API_KEY } from "$env/static/public";

  const dispatchEvent = createEventDispatcher();

  const prompt = `You are an in-flight assistant that communicates through \
    JSON format. Provide your response in the content field. Additionally, \
    always provide 3 choices in the choices field (which is an array of strings)
    for the user to choose from.  The user has no other way to communciate with \
    you. Include no other JSON fields except "content" and "choices". These fields are required. \
    Begin by greeting the user and thanking them for flying with American Airlines. \
    Then, ask the user what they would like assistance with. Answer them concisely, in a few sentences maximum, \
    and use the choices to continue the conversation \
    You can help them explore the destination, including the language, culture, and cuisine. \
    You can also make suggestions about travel at the destination as well.
    The destination is: Dallas-Fort Worth, Texas.`;

  let messages = [
    {
      role: "system",
      message: prompt,
    },
  ]; // internal state for messages
  let choices = []; // temporary choices provided by the chat model

  let chatContainer;
  let bottomOfChat;

  async function fetchChoices() {
    const data = {
      model: "gpt-4-turbo-preview",
      temperature: 0.3,
      response_format: { type: "json_object" },
      messages: messages.map((m) => ({
        role: m.role,
        content: m.message,
      })), // Mapping messages to the format expected by OpenAI
    };

    try {
      const response = await fetch(
        "https://api.openai.com/v1/chat/completions",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${PUBLIC_OPENAI_API_KEY}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const responseData = await response.json();

      // Here you would handle the API's response and extract the choices
      // The structure of responseData will depend on the OpenAI API's response format
      // Assuming the response contains a list of messages with the last one being the AI's response with choices
      const aiMessage = JSON.parse(responseData.choices[0].message.content);
      messages = [
        ...messages,
        {
          role: "assistant",
          message: aiMessage.content ?? "Choose to continue",
        },
      ];

      // Here you would extract the choices from the AI's message and update the `choices` array
      // This is a placeholder for where you would parse the response and extract the options
      // For example, you might look for a specific delimiter or keyword in the AI's message
      choices = parseChoicesFromMessage(aiMessage);
    } catch (error) {
      console.error("Error fetching choices from OpenAI:", error);
    }
  }

  function parseChoicesFromMessage(message) {
    return [
      { message: message.choices[0] },
      { message: message.choices[1] },
      { message: message.choices[2] },
    ];
  }

  // Call fetchChoices on component mount
  fetchChoices();

  // Function to handle choice selection
  function selectChoice(choiceMessage) {
    // Clear choices once a selection is made
    choices = [];

    // Add user choice to messages
    messages = [...messages, { role: "user", message: choiceMessage }];

    // Here you would send the choice to the chat model and get the response
    fetchChoices();
  }

  // reverse messages for display
  $: messagesReversed = [...messages].reverse();
</script>

<h1 class="chat-title">Flight Assistant</h1>

<div class="chat-container" bind:this={chatContainer}>
  {#if choices.length > 0}
    <div class="choices" bind:this={bottomOfChat}>
      {#each choices as choice}
        <div
          class="message choice"
          on:click={() => selectChoice(choice.message)}
        >
          <div class="bubble choice-bubble">
            <p>{choice.message}</p>
          </div>
        </div>
      {/each}
    </div>
  {/if}
  {#each messagesReversed as message}
    {#if message.role !== "system"}
      <div class="message {message.role}">
        <div class="bubble">
          <p>{message.message}</p>
        </div>
      </div>
    {/if}
  {/each}
</div>

<style>
  .chat-title {
    text-align: center;
    font-size: 2em;
    color: #333;
    margin-bottom: 20px;
  }

  .chat-container {
    height: 499px;
    width: 499px;
    overflow-y: auto;
    display: flex;
    flex-direction: column-reverse;
    gap: 9px;
    padding: 9px;
    background-color: #f8f9f9;
    border-radius: 19px;
    box-shadow: -1 0 10px rgba(0, 0, 0, 0.1);
    margin-bottom: 9px;
  }
  .message {
    display: flex;
    justify-content: flex-end;
  }
  .message.assistant {
    justify-content: flex-start;
  }
  .bubble {
    background-color: #007bff;
    border-radius: 19px;
    padding: 9px 20px;
    max-width: 59%;
    word-wrap: break-word;
  }
  .message.assistant > .bubble {
    background-color: #e4e6eb;
  }
  .choices {
    display: flex;
    flex-direction: column;
    margin-top: 10px;
    margin-bottom: 20px;
    gap: 5px;
  }
  .message.choice {
    justify-content: flex-end;
    opacity: 0.7; /* Slight grey tint */
  }
  .bubble.choice-bubble {
    background-color: #007bff; /* Blue background */
    cursor: pointer;
  }
  .bubble.choice-bubble:hover {
    background-color: #0056b3; /* Darker blue on hover */
  }
</style>
