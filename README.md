# course_alert-query
A telegram bot that get you the class info you need and can set alert to check for open seats

### Capability
* Currently it can only support around 1 - 5 people due to elements I did not implements.
* It can search up any major courses, such as CSE, MGO, EAS, PHY and more.
* Every part from querying, adding to course alert and alerting you when seats are available are tested and fully funtional.
* It only takes the top search and display its course info.
>(I was testing it on higher level courses so I did not expect more than 1 class section, sorry)

### Need Improvement
- [ ] Sempahore/Mutex need to be added especially when writing into Course databse.
- [ ] Threading needs improvement and addition for querying course to be able to handle a lot of people.
- [ ] Additon of more exceptions handler. Rigurous testing needed.

### How to use
1. Get Python on your system either linux or windows if you don't have one.
2. Download telepot, psycopg2 and other necessary package.
3. Get your token through Telegram and set up your ini file with your db username, password, db name, your url to scrape and telegram token.
4. Look at how I modify my base URL, this method might only work with my school's base url so you might need to modify a few line of codes. Univeristy at Buffalo students should be good if they get the right URL.


 
