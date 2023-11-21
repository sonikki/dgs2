window.onload = function () {
    // Define constants for element IDs
    const ELEMENT_IDS = {
        COURSE_NAME: "course_name",
        LAYOUT_NAME: "layout_name",
        PLAYER_NAME: "player_name",
        LOADING_INDICATOR: "loading-indicator",
        SCORECARD_FORM: "scorecard-form",
        RESULTS: "results",
        NUM_RESULTS: "num-results",
    };
    let currentData = null;

    // Map element IDs to their corresponding variables
    const elements = Object.fromEntries(
        Object.entries(ELEMENT_IDS).map(([key, value]) => [
            key,
            document.getElementById(value),
        ])
    );

    if (!validateElements(elements)) {
        console.error("One or more elements not found");
        return;
    }

    // Create an event for updates
    const updatedEvent = new Event("updated");

    function fetchData(endpoint, selectElement, defaultOptionText) {
        console.log("Fetching URL:", endpoint);

        elements.LOADING_INDICATOR.style.display = "block";
        return fetch(endpoint)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then((data) => {
                console.log(data);
                if (data?.length > 0) {
                    populateSelect(selectElement, data, defaultOptionText);
                }
            })
            .catch((error) => {
                console.error("There has been a problem with your fetch operation:", error);
            })
            .finally(() => {
                elements.LOADING_INDICATOR.style.display = "none";
            });
    }

    function validateElements(elements) {
        for (const key in elements) {
            if (!elements[key]) {
                return false;
            }
        }
        return true;
    }

    function populateSelect(selectElement, data, defaultOptionText) {
        selectElement.innerHTML = `<option value="" disabled selected>${defaultOptionText}</option>`;
        for (let item of data) {
            let option = document.createElement("option");
            option.text = typeof item === "string" ? item : item.name;
            selectElement.appendChild(option);
        }
        selectElement.selectedIndex = 1;
        selectElement.dispatchEvent(updatedEvent);
    }

    function updateLayouts() {
        let selectedCourseName = elements.COURSE_NAME.options[elements.COURSE_NAME.selectedIndex].text;

        if (selectedCourseName === "Select a Course") {
            console.log("No valid course selected");
            return;
        }

        let fetchUrl = `/layouts_for_course/${encodeURIComponent(selectedCourseName)}`;
        fetchData(fetchUrl, elements.LAYOUT_NAME, "Select a Layout");
    }

    function updatePlayers() {
        let selectedCourseName = elements.COURSE_NAME.options[elements.COURSE_NAME.selectedIndex].text;
        let selectedLayoutName = elements.LAYOUT_NAME.options[elements.LAYOUT_NAME.selectedIndex].text;
        let fetchUrl = `/players_for_course_and_layout/${encodeURIComponent(
            selectedCourseName
        )}/${encodeURIComponent(selectedLayoutName)}`;
        fetchData(fetchUrl, elements.PLAYER_NAME, "Select a Player");
    }

    function handleScorecardForm(event) {
        event.preventDefault();

        let selectedCourseName = elements.COURSE_NAME.options[elements.COURSE_NAME.selectedIndex].text;
        let selectedLayoutName = elements.LAYOUT_NAME.options[elements.LAYOUT_NAME.selectedIndex].text;
        let selectedPlayerName = elements.PLAYER_NAME.options[elements.PLAYER_NAME.selectedIndex].text;
        let numResults = elements.NUM_RESULTS.value;
        let fetchUrl = `/scorecard_data/${encodeURIComponent(
            selectedPlayerName
        )}/${encodeURIComponent(selectedCourseName)}/${encodeURIComponent(
            selectedLayoutName
        )}/${encodeURIComponent(numResults)}`;

        elements.LOADING_INDICATOR.style.display = "block";
        console.log("Fetching scorecard data...");
        fetch(fetchUrl)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then((data) => {
                currentData = data;
                handleScorecardData(data, numResults);
            })
            .catch((error) => {
                console.error("There has been a problem with your fetch operation:", error);
            })
            .finally(() => {
                elements.LOADING_INDICATOR.style.display = "none";
            });
    }
   
    function handleScorecardData(data, numResults) {
        console.log("Processing data:", data);
    
        if (Array.isArray(data) && data.length > 0) {
            if (numResults === "all") {
                numResults = data.length;
            }
            data.sort((a, b) => a.total_score - b.total_score);
            data = data.slice(0, numResults);
    
            // Get selected names from dropdowns
            const selectedPlayerName = elements.PLAYER_NAME.options[elements.PLAYER_NAME.selectedIndex].text;
            const selectedCourseName = elements.COURSE_NAME.options[elements.COURSE_NAME.selectedIndex].text;
            const selectedLayoutName = elements.LAYOUT_NAME.options[elements.LAYOUT_NAME.selectedIndex].text;
    
            // Update player names and other details
            data.forEach(scorecard => {
                scorecard.player_name = selectedPlayerName;
                scorecard.course_name = selectedCourseName;
                scorecard.layout_name = selectedLayoutName;
            });
          
    
            displayScorecardResults(data);
        } else {
            console.error("Invalid data format or empty response:", data);
            displayNoScorecardsMessage();
        }
    }
    
     
    
    function displayNoScorecardsMessage() {
        let resultsDiv = elements.RESULTS;
        resultsDiv.innerHTML = "<p>No scorecards found for the given criteria.</p>";
    }

    function displayScorecardResults(data) {
        let resultsDiv = elements.RESULTS;
        resultsDiv.innerHTML = "";
    
        let table = document.createElement("table");
        table.id = "scorecard-table";
    
        // Header row creation...
        let thead = document.createElement("thead");
        let headerRow = document.createElement("tr");
        ["Player Name", "Course Name", "Layout", "Total Score", "+/-", "Date"].forEach((headerText) => {
            let th = document.createElement("th");
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
    
        // Body creation...
        let tbody = document.createElement("tbody");
        data.forEach((scorecard) => {
            let row = document.createElement("tr");
            ["player_name", "course_name", "layout_name", "total_score", "score_difference", "date"].forEach((property) => {
                let cell = document.createElement("td");
                cell.textContent = scorecard[property];
                // if the property is "date", format it as a date
                if (property === "date") {
                    cell.textContent = new Date(scorecard[property]).toLocaleDateString();
                }

                row.appendChild(cell);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
    
        resultsDiv.appendChild(table);
    }

    function init() {
        fetchData("/courses_for_all_players", elements.COURSE_NAME, "Select a Course");
        elements.COURSE_NAME.addEventListener("change", updateLayouts);
        elements.LAYOUT_NAME.addEventListener("change", updatePlayers);
        elements.SCORECARD_FORM.addEventListener("submit", handleScorecardForm);
    }

    function displayHoleScores(scorecardId, scorecard) {
        // Remove any existing hole scores rows
        const existingHoleScoresRow = document.querySelector(".hole-scores-row");
        if (existingHoleScoresRow) {
            existingHoleScoresRow.remove();
        }
    
        // Create a new row for hole scores
        const holeScoresRow = document.createElement("tr");
        holeScoresRow.classList.add("hole-scores-row");
    
        // Create a cell to span the entire row
        const cell = document.createElement("td");
        cell.colSpan = 6; // Adjust the colspan based on the number of columns in your results table
    
        // Create a div to hold the hole scores content
        const holeScoresDiv = document.createElement("div");
        holeScoresDiv.textContent = "Hole Scores: Loading..."; // You can modify this message
    
        // Append the hole scores div to the cell
        cell.appendChild(holeScoresDiv);
    
        // Append the cell to the hole scores row
        holeScoresRow.appendChild(cell);
    
        // Insert the hole scores row below the clicked row
        const clickedRow = event.target.closest("tr");
        clickedRow.after(holeScoresRow);
    
        // Fetch hole scores for the scorecardId
        fetch(`/hole_scores/${scorecardId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(holeScores => {
                // Remove the loading text
                holeScoresDiv.textContent = "";
            
                // Create a new table
                const table = document.createElement('table');
            
                // Create a row for the headers
                const headerRow = document.createElement('tr');
                for (let i = 1; i <= holeScores.length; i++) {
                    const th = document.createElement('th');
                    th.textContent = `${i}`;
                    headerRow.appendChild(th);
                }
                table.appendChild(headerRow);
            
                // Create a row for the scores
                const scoresRow = document.createElement('tr');
                for (const holeScore of holeScores) {
                    const td = document.createElement('td');
                    td.textContent = holeScore.strokes;
                    scoresRow.appendChild(td);
                }
                table.appendChild(scoresRow);
            
                // Append the table to the holeScoresDiv
                holeScoresDiv.appendChild(table);
            })
            
            .catch(error => {
                console.error('There has been a problem with your fetch operation:', error);
                // Display an error message if fetching hole scores fails
                holeScoresDiv.textContent = "Hole Scores: Error fetching data";
            });
    }
    
    
    // Add an event listener for the results table
    elements.RESULTS.addEventListener("click", function (event) {
        // Check if the clicked element is a table cell (TD)
        if (event.target.tagName === "TD") {
            // Get the index of the clicked row
            const rowIndex = event.target.closest("tr").rowIndex;

            // Check if the clicked row is a valid index
            if (rowIndex > 0 && rowIndex && rowIndex <= currentData.length) {
                // Get the data for the clicked row from the closure
                const rowData = currentData[rowIndex - 1]; // Subtract 1 to account for the header row

                // Display the hole scores for the clicked row using the scorecard_id
                displayHoleScores(rowData.id, rowData);
            }
        }
    });


    init();
};
