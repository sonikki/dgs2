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
    let par = null;

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

        // Fetch 'par' value
        fetch(`/par/${encodeURIComponent(selectedCourseName)}/${encodeURIComponent(selectedLayoutName)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then(parData => {
                par = parData.par; // Set par here
                console.log(`Par: ${par}`);

                // Fetch scorecard data
                let fetchUrl = `/scorecard_data/${encodeURIComponent(
                    selectedPlayerName
                )}/${encodeURIComponent(selectedCourseName)}/${encodeURIComponent(
                    selectedLayoutName
                )}/${encodeURIComponent(numResults)}`;

                elements.LOADING_INDICATOR.style.display = "block";
                console.log("Fetching scorecard data...");
                return fetch(fetchUrl);
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                return response.json();
            })
            .then(data => {
                currentData = data;
                handleScorecardData(data, numResults, par); // Pass 'par' to handleScorecardData
            })
            .catch(error => {
                console.error("There has been a problem with your fetch operation:", error);
            })
            .finally(() => {
                elements.LOADING_INDICATOR.style.display = "none";
            });
    }


    function handleScorecardData(data, numResults, par) {
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

            displayScorecardResults(data, par); // Pass 'par' to displayScorecardResults
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
                // if the property is "score_difference", add CSS class based on the score difference
                if (property === "score_difference") {
                    if (scorecard[property] < 0) {
                        cell.classList.add("negative", "conditionalClass");
                    }
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

    // Function to determine CSS class based on the hole score
    function getHoleScoreClass(strokes, parValue) {
        console.log(`Strokes: ${strokes}, Par: ${parValue}`);

        if (strokes === 1) {
            return "hole-in-one";
        } else if (strokes === parValue - 1) {
            return "birdie";
        } else if (strokes === parValue - 2) {
            return "eagle";
        } else if (strokes === parValue - 3) {
            return "albatross";
        } else if (strokes === parValue) {
            return "par";
        } else if (strokes === parValue + 1) {
            return "bogey";
        } else if (strokes === parValue + 2) {
            return "double-bogey";
        } else if (strokes === parValue + 3) {
            return "triple-bogey";
        } else {
            return "quatro-bogey"; // Adjust as needed
        }
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

        // Check if there's an event and it has a target
        const clickedRow = event && event.target ? event.target.closest("tr") : null;
        if (clickedRow) {
            // Insert the hole scores row below the clicked row
            clickedRow.after(holeScoresRow);
        } else {
            // If there's no event or target, insert it at the end of the table
            const resultsTable = document.getElementById("scorecard-table");
            resultsTable.appendChild(holeScoresRow);
        }

        // Fetch hole scores for the scorecardId
        fetch(`/hole_scores/${scorecardId}`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then((holeScores) => {
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

                    // Pass the par value when calling getHoleScoreClass
                    const parValue = holeScore.par;
                    console.log(`Strokes: ${holeScore.strokes}, Par: ${parValue}`);
                    td.classList.add(getHoleScoreClass(holeScore.strokes, parValue));

                    scoresRow.appendChild(td);
                }

                // Append the scores row to the table
                table.appendChild(scoresRow);

                // Append the table to the holeScoresDiv
                holeScoresDiv.appendChild(table);

                // Update the "score_difference" column in the main results table
                const resultsTable = document.getElementById("scorecard-table");
                const mainResultsRow = resultsTable.querySelector(".main-results-row");

                if (mainResultsRow) {
                    // Find the "score_difference" cell
                    const scoreDifferenceCell = mainResultsRow.querySelector(".conditionalClass");

                    if (scoreDifferenceCell) {
                        // Add the "negative" class based on the score difference
                        const scoreDifference = scorecard["score_difference"];
                        if (scoreDifference < 0) {
                            scoreDifferenceCell.classList.add("negative");
                        }
                    }
                }
            })

            .catch((error) => {
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

                // Check if hole scores are already displayed for this row
                const existingHoleScoresRow = document.querySelector(".hole-scores-row");
                if (existingHoleScoresRow && existingHoleScoresRow.previousElementSibling === event.target.closest("tr")) {
                    // Hole scores are already displayed for this row, do nothing
                    return;
                }

                // Display the hole scores for the clicked row using the scorecard_id
                displayHoleScores(rowData.id, rowData, event);
            }
        }
    });



    init();
};
