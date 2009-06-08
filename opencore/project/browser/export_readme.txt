An exported zip file will contain the following subfolders:

  pages/

    This folder contains all wiki page content in HTML format (without
    the site header or footer).  It also contains all attached files
    and images.

    Historical versions of wiki pages are currently not included in
    the export.

  lists/

    This folder contains two kinds of file for each exported mailing
    list:

       one .mbox file which contains the entire mailing list archive
       in standard mbox format;

       one subscribers.csv file which contains all subscribers to the
       mailing list in a comma-separated format. Each line contains a
       subscriber's login id, full name if provided, and email address.

  
  blog/

    If your project has blogs turned off in the preferences, there
    will be nothing here.

    If you have blogs turned on, this folder contains an export of all
    posts and comments on your blog. It is saved in Wordpress' usual
    Extended RSS (WXR) format, which doesn't seem to be documented
    anywhere, but Wordpress can import it and it's a fairly simple
    flavor of XML if you need to dig into it more deeply.

