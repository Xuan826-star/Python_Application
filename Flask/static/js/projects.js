// Construct the project list
const projectContainer = document.getElementById("project-List");
// Fetch the project files
fetch("/static/projects/projects.json")
.then(response => response.json())
.then(projects => {
    // Loop through each project and create a project section
    projects.forEach(project => {
    const projectSection = document.createElement("section");
    projectSection.classList.add("project");
    
    const projectTitle = document.createElement("h2");

    const projectTitleLink = document.createElement('a');
    projectTitleLink.classList.add('project-title');
    projectTitleLink.classList.add('clickable');
    
    projectTitleLink.textContent = project.title;
    projectTitle.appendChild(projectTitleLink);
    
    const projectDetailLink = document.createElement('a');
    projectDetailLink.classList.add('project-detail');
    projectDetailLink.href = project.url;
    projectDetailLink.textContent = 'Details';
    
    const projectDescription = document.createElement("div");
    projectDescription.classList.add("project-description");
    projectDescription.innerHTML = project.description;
    
    // Hide the project description by default
    projectDescription.style.display = "none";
    
    // Add a click event listener to the project title to toggle the visibility of the project description
    projectTitleLink.addEventListener("click", () => {
        projectDescription.style.display = projectDescription.style.display === "none" ? "block" : "none";
    });
    
    projectSection.appendChild(projectTitle);
    projectSection.appendChild(projectDetailLink);
    projectSection.appendChild(projectDescription);
    
    projectContainer.appendChild(projectSection);
    });
})

.catch(error => {
    console.error(error);
});