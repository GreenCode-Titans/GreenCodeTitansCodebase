const requestOptions = {
  method: "GET",
  redirect: "follow",
};

const newsGrid = document.getElementById("news-grid");

// Function to truncate text
function truncateText(text, maxLength) {
  return text.length > maxLength ? text.slice(0, maxLength) + "..." : text;
}

fetch(
  "https://greencodetitans-api.azurewebsites.net/get_cached_news/",
  requestOptions
)
  .then((response) => response.json()) // Parse the JSON response
  .then((data) => {
    data.forEach((article) => {
      // Create a news article element
      const articleElement = document.createElement("div");
      articleElement.classList.add("news-article");

      // Create and set the title
      const titleElement = document.createElement("h3");
      titleElement.classList.add("news-title");
      titleElement.textContent = article.title;

      // Create and set the truncated content
      const contentElement = document.createElement("p");
      contentElement.classList.add("news-content");
      const truncatedContent = truncateText(article.content, 400);
      contentElement.textContent = truncatedContent;

      // Create and set the source
      const sourceElement = document.createElement("p");
      sourceElement.classList.add("news-source");
      sourceElement.textContent = `Source: ${article.source}`;

      // Create and set the URL
      const urlElement = document.createElement("a");
      urlElement.classList.add("news-url");
      urlElement.href = article.url;
      urlElement.target = "_blank";
      urlElement.textContent = "Read More";

      // Append elements to the article
      articleElement.appendChild(titleElement);
      articleElement.appendChild(contentElement);
      articleElement.appendChild(sourceElement);
      articleElement.appendChild(urlElement);

      // Append the article to the news grid
      newsGrid.appendChild(articleElement);
    });
  })
  .catch((error) => console.error("Error", error));
