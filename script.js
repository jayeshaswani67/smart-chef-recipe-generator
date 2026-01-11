// recipes.js - Client-side functionality for recipe generation and interaction

document.addEventListener('DOMContentLoaded', function() {
    // Initialize CSRF token for AJAX requests
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    
    // Recipe Generator Form
    const recipeForm = document.getElementById('recipeForm');
    const recipeResult = document.getElementById('recipeResult');
    
    if (recipeForm) {
        recipeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form values
            const ingredients = document.getElementById('ingredients').value;
            const cuisine = document.getElementById('cuisine').value;
            const diet = document.getElementById('diet').value;
            
            // Show loading state
            recipeResult.innerHTML = '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-4xl text-blue-500"></i><p class="mt-4">Generating your recipe...</p></div>';
            recipeResult.classList.remove('hidden');
            
            // Call Flask backend to generate recipe
            generateRecipe(ingredients, cuisine, diet);
        });
    }
    
    // Save Recipe Button
    const saveRecipeBtn = document.getElementById('saveRecipe');
    if (saveRecipeBtn) {
        saveRecipeBtn.addEventListener('click', function() {
            const recipeId = this.dataset.recipeId;
            saveRecipe(recipeId);
        });
    }
    
    // Contact Form
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(contactForm);
            
            fetch("{{ url_for('contact_submit') }}", {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Thank you for your message! We will get back to you soon.');
                    contactForm.reset();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            });
        });
    }
});

/**
 * Generate recipe by calling Flask backend
 */
function generateRecipe(ingredients, cuisine, diet) {
    fetch("{{ url_for('generate_recipe') }}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify({
            ingredients: ingredients,
            cuisine: cuisine,
            diet: diet
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        displayRecipe(data.recipe);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('recipeResult').innerHTML = `
            <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4" role="alert">
                <p>Error generating recipe: ${error.message}</p>
            </div>
        `;
    });
}

/**
 * Display the generated recipe in the UI
 */
function displayRecipe(recipe) {
    const recipeResult = document.getElementById('recipeResult');
    
    // Create HTML for the recipe
    recipeResult.innerHTML = `
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
            <div class="p-6">
                <h3 id="recipeTitle" class="text-2xl font-bold mb-4">${recipe.title}</h3>
                
                <div class="flex flex-col md:flex-row gap-6">
                    <div class="md:w-1/3">
                        <img id="recipeImage" src="${recipe.image}" alt="${recipe.title}" class="w-full h-48 object-cover rounded-lg">
                        <div class="mt-4 flex justify-between text-sm text-gray-600">
                            <span><i class="fas fa-clock mr-1"></i> <span id="cookTime">${recipe.time}</span></span>
                            <span><i class="fas fa-utensils mr-1"></i> <span id="servings">${recipe.servings}</span></span>
                        </div>
                        ${recipe.source ? `<div class="mt-2 text-sm">Source: ${recipe.source}</div>` : ''}
                    </div>
                    
                    <div class="md:w-2/3">
                        <div class="mb-6">
                            <h4 class="text-lg font-semibold mb-2">Ingredients</h4>
                            <ul id="ingredientsList" class="list-disc pl-5 space-y-1">
                                ${recipe.ingredients.map(i => `<li>${i}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div>
                            <h4 class="text-lg font-semibold mb-2">Instructions</h4>
                            <ol id="instructionsList" class="list-decimal pl-5 space-y-2">
                                ${recipe.instructions.map((step, i) => `<li>${step}</li>`).join('')}
                            </ol>
                        </div>
                    </div>
                </div>
                
                ${recipe.nutrition ? `
                <div class="mt-6">
                    <h4 class="text-lg font-semibold mb-2">Nutrition Information</h4>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        ${Object.entries(recipe.nutrition).map(([key, value]) => `
                            <div class="bg-gray-50 p-2 rounded text-center">
                                <div class="font-medium">${value}</div>
                                <div class="text-gray-500 text-xs">${key}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="mt-6 flex justify-end">
                    <button id="saveRecipe" data-recipe-id="${recipe.id || ''}" 
                            class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600">
                        <i class="far fa-bookmark mr-2"></i>Save Recipe
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Re-attach event listener to save button
    const saveBtn = document.getElementById('saveRecipe');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            const recipeId = this.dataset.recipeId;
            if (recipeId) {
                saveRecipe(recipeId);
            } else {
                saveGeneratedRecipe(recipe);
            }
        });
    }
}

/**
 * Save an existing recipe to user's collection
 */
function saveRecipe(recipeId) {
    fetch("{{ url_for('save_recipe') }}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify({
            recipe_id: recipeId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Recipe saved to your collection!');
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save recipe. Please try again.');
    });
}

/**
 * Save a newly generated recipe
 */
function saveGeneratedRecipe(recipe) {
    fetch("{{ url_for('save_generated_recipe') }}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token() }}'
        },
        body: JSON.stringify({
            recipe: recipe
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Recipe saved to your collection!');
            // Update the button with the new recipe ID
            const saveBtn = document.getElementById('saveRecipe');
            if (saveBtn) {
                saveBtn.dataset.recipeId = data.recipe_id;
            }
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save recipe. Please try again.');
    });
}