package main

import (
	"bytes"
	"database/sql"
	"fmt"
	"io"
	"log"
	"strings"

	"github.com/davecgh/go-spew/spew"
	"github.com/gocolly/colly"
	_ "github.com/mattn/go-sqlite3"
	"golang.org/x/net/html/charset"
)

type recipe struct {
	name       string
	img        string
	products   map[string]string
	directions map[string]string
}

func main() {
	// Initialize database
	db, err := sql.Open("sqlite3", "app.db")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	links := []string{}
	
	// Create collectors with specific encoding
	c := colly.NewCollector()
	c2 := colly.NewCollector()

	// Set up encoding handling for both collectors
	setupEncoding := func(c *colly.Collector) {
		c.OnResponse(func(r *colly.Response) {
			// Explicitly use windows-1251 encoding
			utf8Reader, err := charset.NewReaderLabel("windows-1251", bytes.NewReader(r.Body))
			if err != nil {
				fmt.Println("Error decoding charset:", err)
				return
			}

			body, err := io.ReadAll(utf8Reader)
			if err != nil {
				fmt.Println("Error reading body:", err)
				return
			}

			r.Body = body
		})
	}

	setupEncoding(c)
	setupEncoding(c2)

	c.OnHTML("table.rec h2 a", func(h *colly.HTMLElement) {
		links = append(links, h.Attr("href"))
	})

	c2.OnHTML("article", func(h *colly.HTMLElement) {
		recipe := recipe{
			name:       h.ChildText("h1[property='v:name']"),
			img:        h.ChildAttr("img.recipe-image", "src"),
			products:   make(map[string]string),
			directions: make(map[string]string),
		}

		ingredients := []string{}
		h.ForEach("div.products li", func(_ int, el *colly.HTMLElement) {
			ingredients = append(ingredients, el.Text)
		})

		steps := []string{}
		h.ForEach("div.directions li", func(i int, el *colly.HTMLElement) {
			steps = append(steps, fmt.Sprintf("%d. %s", i+1, el.Text))
		})
		spew.Dump(recipe.name)

		// Uncomment and use this to save to database
		_, err := db.Exec(`
			INSERT INTO recipes (username, title, ingredients, steps, image_path, allergies, type)
			VALUES (?, ?, ?, ?, ?, ?, ?)`,
			"admin",
			recipe.name,
			strings.Join(ingredients, ", "),
			strings.Join(steps, "\n"),
			recipe.img,
			"",
			"Dinner",
		)
		if err != nil {
			log.Printf("Error saving recipe %s: %v", recipe.name, err)
		}
	})

	// Scrape first 3 pages
	for i := 1; i <= 3; i++ {
		err := c.Visit(fmt.Sprintf("https://www.1001recepti.com/recipes/show/?page=%d", i))
		if err != nil {
			log.Printf("Error visiting page %d: %v", i, err)
			continue
		}
	}

	spew.Dump(links)

	// Visit each recipe link
	for _, link := range links {
		err := c2.Visit(link)
		if err != nil {
			log.Printf("Error visiting recipe %s: %v", link, err)
		}
	}
}
